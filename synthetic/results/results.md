# Embedding benchmark results

Corpus: 42 chunks. Answerable queries: 13. No-answer queries: 3. max_seq_length=512, batch_size=16.

## Summary

| Model | Device / dtype | Dim | R@1 | R@3 | R@5 | MRR@10 | Doc@1 | Query p50 ms | Query p95 ms | Chunks/s | Peak RAM MB | Peak VRAM MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| minilm-l6 | cuda / float16 | 384 | 0.923 | 1.000 | 1.000 | 0.962 | 1.000 | 4.3 | 5.2 | 2048.8 | 1516 | 64 |
| bge-small-en | cuda / float16 | 384 | 0.923 | 0.923 | 1.000 | 0.938 | 0.923 | 7.4 | 8.3 | 1524.1 | 1558 | 86 |

Chunks/s is measured on chunks averaging the token counts below; longer chunks are slower.

| Model | Mean tokens/chunk | Tokens/s | Load s |
|---|---|---|---|
| minilm-l6 | 52 | 106049 | 104.0 |
| bge-small-en | 52 | 78891 | 94.9 |

## Recall@1 / MRR@10 by query type

| Model | exact | long | paraphrased | short | similar-document | technical |
|---|---|---|---|---|---|---|
| minilm-l6 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.67 / 0.83 | 1.00 / 1.00 |
| bge-small-en | 1.00 / 1.00 | 0.50 / 0.60 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |

## No-answer queries

A usable model keeps answerable queries above the threshold and no-answer queries below it. The threshold is fitted on this same small set, so treat it as a starting point.

| Model | Mean top-1 (answerable) | Min top-1 (answerable) | Max top-1 (no-answer) | Threshold | No-answer rejected | Answerable kept |
|---|---|---|---|---|---|---|
| minilm-l6 | 0.619 | 0.369 | 0.594 | 0.332 | 0.67 | 1.00 |
| bge-small-en | 0.784 | 0.640 | 0.753 | 0.623 | 0.67 | 1.00 |

## Per-query rank of the first expected chunk (blank = not in top 10)

| Model | Q01 | Q02 | Q03 | Q04 | Q05 | Q06 | Q07 | Q08 | Q09 | Q10 | Q11 | Q12 | Q13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| minilm-l6 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 |
| bge-small-en | 1 | 1 | 1 | 1 | 1 | 1 | 5 | 1 | 1 | 1 | 1 | 1 | 1 |
