# Embedding benchmark results

Corpus: 42 chunks. Answerable queries: 13. No-answer queries: 3. max_seq_length=512, batch_size=16.

## Summary

| Model | Device / dtype | Dim | R@1 | R@3 | R@5 | MRR@10 | Doc@1 | Query p50 ms | Query p95 ms | Chunks/s | Peak RAM MB | Peak VRAM MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gte-modernbert | cuda / float16 | 768 | 0.923 | 1.000 | 1.000 | 0.949 | 1.000 | 13.2 | 19.8 | 592.6 | 1554 | 332 |
| arctic-l-v2 | cuda / float16 | 1024 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 14.2 | 22.2 | 407.3 | 2867 | 1123 |

Chunks/s is measured on chunks averaging the token counts below; longer chunks are slower.

| Model | Mean tokens/chunk | Tokens/s | Load s |
|---|---|---|---|
| gte-modernbert | 54 | 32228 | 138.9 |
| arctic-l-v2 | 58 | 23650 | 222.1 |

## Recall@1 / MRR@10 by query type

| Model | exact | long | paraphrased | short | similar-document | technical |
|---|---|---|---|---|---|---|
| gte-modernbert | 1.00 / 1.00 | 1.00 / 1.00 | 0.50 / 0.67 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| arctic-l-v2 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |

## No-answer queries

A usable model keeps answerable queries above the threshold and no-answer queries below it. The threshold is fitted on this same small set, so treat it as a starting point.

| Model | Mean top-1 (answerable) | Min top-1 (answerable) | Max top-1 (no-answer) | Threshold | No-answer rejected | Answerable kept |
|---|---|---|---|---|---|---|
| gte-modernbert | 0.764 | 0.641 | 0.729 | 0.619 | 0.67 | 1.00 |
| arctic-l-v2 | 0.565 | 0.304 | 0.491 | 0.280 | 0.67 | 1.00 |

## Per-query rank of the first expected chunk (blank = not in top 10)

| Model | Q01 | Q02 | Q03 | Q04 | Q05 | Q06 | Q07 | Q08 | Q09 | Q10 | Q11 | Q12 | Q13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gte-modernbert | 1 | 1 | 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| arctic-l-v2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
