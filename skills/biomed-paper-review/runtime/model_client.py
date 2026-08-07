#!/usr/bin/env python3
"""模型客户端抽象：**每次调用都是独立的一次，不携带任何对话历史。**

这是整个分层运行时成立的前提。上一版架构失败的原因不是规范写得不好，
而是所有「阶段」都发生在同一个模型上下文里 —— 提示词里写「现在做发现」
「现在扮演 M4」，本质上仍是一次单体执行：前一阶段的全部内容仍在上下文中，
注意力仍然被它占着。

因此本类**刻意不提供**多轮对话接口。`complete()` 每次都从零开始：
系统提示 + 本次输入，没有 messages 列表，没有 session id，没有续接。
想让两个阶段共享信息，只能通过**显式的结构化产物**传递，
而那正是我们要的 —— 接口可见、可校验、可度量。

配置走环境变量，不写死任何供应商：

    BIOMED_REVIEW_PROVIDER   dashscope | openai | zhipu | moonshot   （默认 dashscope）
    BIOMED_REVIEW_MODEL      模型名（默认按供应商给一个）
    BIOMED_REVIEW_BASE_URL   覆盖端点（可选）
    <PROVIDER>_API_KEY       对应的密钥环境变量

**不要在代码里编造密钥。** 缺密钥时明确报错，而不是静默降级 ——
静默降级会让「没跑起来」被误读成「跑了但没发现问题」。
"""

import json
import os
import time
import urllib.error
import urllib.request

# 各供应商的 OpenAI 兼容端点。都走 /chat/completions，差别只在 base_url 与密钥变量。
PROVIDERS = {
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "key_env": "DASHSCOPE_API_KEY",
        "default_model": "qwen3.8-max",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "key_env": "ZHIPUAI_API_KEY",
        "default_model": "glm-4-plus",
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "key_env": "MOONSHOT_API_KEY",
        "default_model": "moonshot-v1-32k",
    },
}


class ModelUnavailable(RuntimeError):
    """密钥缺失或端点不可达。

    **这是我们的能力限制，不是稿件的问题** —— 调用方必须把它登记成
    system_limitation，绝不能当作「审阅完成且没发现问题」。
    """


class ModelResponse:
    def __init__(self, text, parsed=None, raw=None, elapsed=0.0):
        self.text = text
        self.parsed = parsed          # response_schema 非空且解析成功时为 dict
        self.raw = raw
        self.elapsed = elapsed

    def __repr__(self):
        return f"<ModelResponse {len(self.text or '')} chars in {self.elapsed:.1f}s>"


class ModelClient:
    """无状态模型客户端。

    每个 `complete()` 都是一次全新的调用。**没有跨阶段的上下文继承。**
    """

    def __init__(self, provider=None, model=None, base_url=None,
                 timeout=600, max_retries=2, telemetry=None):
        self.provider = (provider or os.environ.get("BIOMED_REVIEW_PROVIDER")
                         or "dashscope").lower()
        if self.provider not in PROVIDERS:
            raise ModelUnavailable(
                f"未知供应商 {self.provider!r}；可选：{sorted(PROVIDERS)}")
        cfg = PROVIDERS[self.provider]
        self.model = model or os.environ.get("BIOMED_REVIEW_MODEL") or cfg["default_model"]
        self.base_url = (base_url or os.environ.get("BIOMED_REVIEW_BASE_URL")
                         or cfg["base_url"]).rstrip("/")
        self.key_env = cfg["key_env"]
        self.timeout = timeout
        self.max_retries = max_retries
        self.telemetry = telemetry

    def _api_key(self):
        k = os.environ.get(self.key_env)
        if not k:
            raise ModelUnavailable(
                f"缺少 {self.key_env}。请设置后重试 —— "
                f"**不得**因为缺密钥就跳过该阶段并当作没有发现问题。")
        return k

    def complete(self, system_prompt, user_content, response_schema=None,
                 metadata=None, stage=None, module=None):
        """一次独立调用。

        `user_content` 可以是字符串或 dict；dict 会被序列化成 JSON，
        这样各阶段之间传的是**显式结构化接口**而不是自然语言黏合。
        """
        if not isinstance(user_content, str):
            user_content = json.dumps(user_content, ensure_ascii=False, indent=1)

        sys_prompt = system_prompt
        if response_schema:
            # 要求结构化输出。不用供应商私有的 json_schema 参数 ——
            # 各家支持程度不一，改用提示约束 + 本地解析，可移植性更好。
            sys_prompt += (
                "\n\n## 输出格式（强制）\n"
                "只输出一个 JSON 对象，不要任何解释文字、不要 markdown 代码围栏。\n"
                "必须符合以下 JSON Schema：\n"
                + json.dumps(response_schema, ensure_ascii=False))

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content},
            ],
        }

        t0 = time.time()
        text, err = self._post(body)
        elapsed = time.time() - t0

        if err:
            if self.telemetry:
                self.telemetry.record_call(
                    stage=stage, module=module, model=self.model,
                    status="failed", elapsed=elapsed, metadata=metadata, error=err)
            raise ModelUnavailable(f"调用失败：{err}")

        parsed = _extract_json(text) if response_schema else None
        if self.telemetry:
            self.telemetry.record_call(
                stage=stage, module=module, model=self.model,
                status="ok" if (parsed is not None or not response_schema) else "unparsed",
                elapsed=elapsed, metadata=metadata,
                output_chars=len(text or ""))
        return ModelResponse(text=text, parsed=parsed, elapsed=elapsed)

    def _post(self, body):
        url = f"{self.base_url}/chat/completions"
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self._api_key()}"}
        last = None
        for i in range(self.max_retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    d = json.loads(r.read().decode("utf-8", "replace"))
                return d["choices"][0]["message"]["content"], None
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:300]
                last = f"HTTP {e.code}: {detail}"
                if e.code not in (429, 500, 502, 503, 504):
                    return None, last
            except Exception as exc:                             # noqa: BLE001
                last = f"{type(exc).__name__}: {str(exc)[:200]}"
            if i < self.max_retries:
                time.sleep(3 * (i + 1))
        return None, last


def _extract_json(text):
    """从模型输出里取出 JSON。

    容忍两种常见包装：markdown 代码围栏，以及 JSON 前后的解释文字。
    取不出来返回 None —— **不猜、不修补**，让调用方按「未产出结构化结果」处理。
    """
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if t.count("```") >= 2 else t
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    try:
        return json.loads(t.strip())
    except ValueError:
        pass
    start = t.find("{")
    if start < 0:
        return None
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(t[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(t[start:i + 1])
                except ValueError:
                    return None
    return None
