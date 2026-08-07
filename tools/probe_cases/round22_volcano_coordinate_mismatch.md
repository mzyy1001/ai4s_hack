# Differential-expression methods

Genes were called significant when `FDR < 0.05` and `|log2 fold change| >= 1`.
The volcano plot uses `log2 fold change` on the x-axis and `-log10(FDR)` on the
y-axis. Significant up-regulated genes are red and significant down-regulated
genes are blue.

# Supplementary source-data rows and rendered Figure 4 coordinates

| Gene | log2 fold change | FDR | Rendered x | Rendered y | Rendered class |
| --- | ---: | ---: | ---: | ---: | --- |
| STAT1 | 1.48 | 0.0020 | 1.48 | 0.70 | red significant |
| CXCL8 | 2.00 | 0.0100 | -2.00 | 2.00 | blue significant |
| GAPDH | 0.20 | 0.4000 | 0.20 | 0.40 | grey nonsignificant |

The horizontal threshold is drawn at y = 1.30 and vertical thresholds at
x = -1 and x = 1. The Results identify STAT1 and CXCL8 as representative
up-regulated genes in Figure 4.
