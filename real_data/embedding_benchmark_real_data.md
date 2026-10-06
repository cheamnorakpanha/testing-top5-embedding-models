# Embedding Model Benchmark: Real HRD Data

Owner: Panha · Date: 2026-10-06 · Status: **measured on the RTX 3060 with real HRD workbooks (405 chunks, 70 questions)**

> This report follows `synthetic/embedding_benchmark.md`, which selected candidates and tested them on a synthetic corpus. The picks below replace the ones in that report.

## 1. Bottom line

| Role              | Model                                     | Why                                                                                                                                                                                                                                           |
| ----------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Primary**       | `BAAI/bge-m3`                             | Best or tied for best on real HRD data: the right row in the top 3 for 58 of 60 questions (0.967) and the highest MRR (0.902). MIT licence, not gated. It can also produce keyword-style (sparse) vectors, which suits this data (see below). |
| **Backup**        | `BAAI/bge-small-en-v1.5`                  | 49 of 60 at rank 1 against 51 for the primary, and level at rank 5, using 109 MB of VRAM (a tenth of the primary) at nearly five times the indexing speed. The fallback when the GPU is shared with an LLM. English-only, 512-token limit.    |
| Equal alternative | `Snowflake/snowflake-arctic-embed-l-v2.0` | Statistically tied with BGE-M3 (52 of 60 at rank 1, but 54 against 58 in the top 3). Same size, speed and memory. Apache 2.0.                                                                                                                 |
| **Rejected**      | `Alibaba-NLP/gte-modernbert-base`         | The backup on synthetic data, it scored below plain keyword search on real data (0.533 against 0.617 at rank 1) and never found a sheet-description chunk.                                                                                    |

**BGE-M3 was treated as a candidate, not the default, and earned the pick on measurement.** It lost to Arctic by one question on the earlier synthetic test and came out level or ahead on real data. The choice between BGE-M3 and Arctic is a tie-break, explained in section 7.

**The real data is spreadsheets, not documents.** The HRD files are attendance and monthly-result workbooks: about 390 student rows across 14 sheets, almost all names, scores and short codes. This has three consequences:

- Retrieval here means finding the right student row in the right sheet. Exact names matter, which is why plain keyword search already puts the right row in the top 5 for 58 of 60 questions, level with the best embedding model. Combining keyword and embedding search is the natural design.
- Questions that need counting, ranking or averaging ("who was absent more than three times") cannot be answered by any embedding model. They need a query over the tables.
- The earlier synthetic test (`embedding_benchmark.md`) was a poor predictor. It put GTE-ModernBERT in a tie for second; on real data it was last.

**How firm this is.** Speed and memory figures are measured on the target GPU. The quality ranking on real data rests on 60 answerable questions, so one question is worth 1.7 points and gaps of one or two questions are ties. The questions were generated from templates, not written by the people who will use the system, and one workbook could not be read (section 3).

## 2. Constraints

- Data and queries: English only. The data turned out to be Excel workbooks of attendance and exam results, not prose documents.
- Hardware: RTX 3060 with 6-8 GB VRAM, run under WSL.
- Documents are confidential, so the model must run fully offline.
- Open question: if the answer-generating LLM shares this GPU, the embedding model's VRAM comes out of the LLM's budget. That favours the backup (109 MB against 1,185 MB on real data).

## 3. The data

|              |                                                                                                                                |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Source       | 3 workbooks, 14 sheets: August 2026 attendance (2 sheets), April monthly result (5), August monthly result (7)                 |
| Chunks       | 405: one per student row (391), written as `Column: value; ...`, plus one description card per sheet (14)                      |
| Chunk length | median 30 words, longest 145; about 90 tokens on average                                                                       |
| Questions    | 70, generated from the data by template: 10 each of exact, paraphrased, short, long, technical, similar-document and no-answer |
| Not included | `Attendance_List_Aug.xls.xls`, which is not an Excel workbook despite its name and could not be read                           |

The same students appear in several sheets, so most questions have near-duplicate rows competing with the right one. "Technical" questions ask what a sheet contains and expect its description card. No-answer questions use invented names.

The workbooks were read in place by `excel_to_corpus.py` and were not modified. Every sheet has the same layout: title lines, a header block, then one row per student. The script turns each student row into one chunk and each sheet into one description card. The data never left the local machine; only the aggregate figures in this report were shared.

## 4. Retrieval questions

70 questions were generated from the data, 10 of each type. They contain student names, so they are kept in `real_data/real/queries.jsonl` on the local machine and are described here by template. The expected document is the workbook, the section is the sheet, and the chunk id is `workbook#sheet#r<Excel row>` for a student row or `workbook#sheet#card` for a sheet description.

| Type             | Template                                                                                | Expected chunk                                                    |
| ---------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Exact            | What is {name}'s {column} in the {sheet} sheet of {workbook}?                           | That student's row in that sheet                                  |
| Paraphrased      | How did {name} do in {sheet}? (four phrasings; no column or workbook given)             | That student's row in that sheet                                  |
| Short            | {name} {sheet}                                                                          | That student's row in that sheet                                  |
| Long             | A three-sentence request naming the workbook, sheet, student and two columns            | That student's row in that sheet                                  |
| Technical        | Which columns are recorded in the {sheet} sheet of {workbook}?                          | The sheet's description card                                      |
| Similar-document | {name}'s result in {sheet} ({workbook}), for students who appear in more than one sheet | The row in the named sheet, not the same student's rows elsewhere |
| No-answer        | What did {invented name} score in {sheet}?                                              | None; the name is not in the data                                 |

## 5. Models and method

|                    | BGE-M3        | Arctic Embed L v2.0                       | bge-small-en-v1.5        | GTE-ModernBERT-base               |
| ------------------ | ------------- | ----------------------------------------- | ------------------------ | --------------------------------- |
| Hugging Face id    | `BAAI/bge-m3` | `Snowflake/snowflake-arctic-embed-l-v2.0` | `BAAI/bge-small-en-v1.5` | `Alibaba-NLP/gte-modernbert-base` |
| Parameters         | ~568M         | 568M                                      | ~33M                     | 149M                              |
| Dimensions         | 1024          | 1024                                      | 384                      | 768                               |
| Max input (tokens) | 8,192         | 8,192                                     | 512                      | 8,192                             |
| Languages          | 100+          | 74                                        | English only             | English only                      |
| Licence            | MIT           | Apache 2.0                                | MIT                      | Apache 2.0                        |
| Query prompt       | No            | Yes (built in)                            | None used                | No                                |

A TF-IDF keyword search was run as a baseline. Qwen3-Embedding-0.6B, Granite English R2 and all-MiniLM-L6-v2, which were measured on the synthetic corpus, were not run on the real data.

- **Recall@k** (k = 1, 3, 5): share of answerable questions with the expected chunk in the top k.
- **MRR@10**: mean of 1 / rank of the expected chunk; 0 if outside the top 10.
- **Doc@1**: share of questions whose top result is from the right workbook.
- **No-answer**: excluded from recall and MRR. The script compares top-1 similarity for answerable and no-answer questions and reports the threshold that best separates them.
- **Latency**: time to embed one query and search, 5 repeats per query after warm-up; p50 and p95.
- **Chunks/sec**: time to embed 2,000 chunks (the corpus repeated) at batch size 16.
- **RAM / VRAM**: peak process memory and peak CUDA memory allocated, one process per model.
- Settings: cosine similarity on normalised vectors, `max_seq_length` 512, each chunk prefixed with workbook and sheet name, fp16 on the GPU. Each model was run once.

## 6. Results

Measured on the RTX 3060 under WSL, 2026-10-06. 60 answerable questions, 10 no-answer questions.

### Summary

| Model                            | R@1       | R@3       | R@5       | MRR@10    | Doc@1 | Query p50 / p95 ms | Chunks/s | Peak RAM MB | Peak VRAM MB |
| -------------------------------- | --------- | --------- | --------- | --------- | ----- | ------------------ | -------- | ----------- | ------------ |
| **BGE-M3**                       | 0.850     | **0.967** | **0.967** | **0.902** | 0.967 | 15.1 / 18.7        | 248.7    | 3,010       | 1,185        |
| Arctic Embed L v2.0              | **0.867** | 0.900     | 0.950     | 0.898     | 0.967 | 15.8 / 21.8        | 253.3    | 3,001       | 1,185        |
| **bge-small-en-v1.5**            | 0.817     | 0.883     | 0.950     | 0.867     | 0.900 | 8.6 / 9.9          | 1,176.9  | 1,519       | 109          |
| TF-IDF baseline (keyword search) | 0.617     | 0.867     | 0.967     | 0.744     | 0.950 | n/a                | n/a      | n/a         | 0            |
| GTE-ModernBERT-base              | 0.533     | 0.750     | 0.817     | 0.644     | 0.883 | 15.4 / 19.9        | 349.2    | 1,562       | 396          |

As counts out of 60 at rank 1 / top 3 / top 5: BGE-M3 51 / 58 / 58, Arctic 52 / 54 / 57, bge-small-en 49 / 53 / 57, TF-IDF 37 / 52 / 58, GTE-ModernBERT 32 / 45 / 49.

### Recall@1 / MRR@10 by query type (10 questions each)

| Model               | Exact       | Paraphrased | Short       | Long        | Technical   | Similar-document |
| ------------------- | ----------- | ----------- | ----------- | ----------- | ----------- | ---------------- |
| BGE-M3              | 0.90 / 0.95 | 0.70 / 0.83 | 1.00 / 1.00 | 0.90 / 0.95 | 0.80 / 0.81 | 0.80 / 0.87      |
| Arctic Embed L v2.0 | 0.90 / 0.93 | 0.70 / 0.80 | 1.00 / 1.00 | 1.00 / 1.00 | 0.60 / 0.66 | 1.00 / 1.00      |
| bge-small-en-v1.5   | 0.90 / 0.93 | 0.40 / 0.59 | 1.00 / 1.00 | 0.90 / 0.95 | 0.70 / 0.73 | 1.00 / 1.00      |
| TF-IDF baseline     | 0.70 / 0.82 | 0.70 / 0.78 | 0.60 / 0.71 | 0.60 / 0.78 | 0.70 / 0.75 | 0.40 / 0.62      |
| GTE-ModernBERT-base | 0.60 / 0.77 | 0.60 / 0.76 | 0.30 / 0.53 | 1.00 / 1.00 | 0.00 / 0.00 | 0.70 / 0.81      |

### No-answer questions

| Model               | Mean top-1 score (answerable) | Lowest top-1 (answerable) | Highest top-1 (no-answer) | Best threshold | No-answer rejected | Answerable kept |
| ------------------- | ----------------------------- | ------------------------- | ------------------------- | -------------- | ------------------ | --------------- |
| BGE-M3              | 0.726                         | 0.529                     | 0.720                     | 0.722          | 10 of 10           | 65%             |
| Arctic Embed L v2.0 | 0.695                         | 0.461                     | 0.622                     | 0.599          | 9 of 10            | 87%             |
| bge-small-en-v1.5   | 0.833                         | 0.641                     | 0.813                     | 0.779          | 9 of 10            | 83%             |
| GTE-ModernBERT-base | 0.826                         | 0.605                     | 0.785                     | 0.793          | 10 of 10           | 72%             |
| TF-IDF baseline     | 0.435                         | 0.244                     | 0.519                     | 0.320          | 7 of 10            | 93%             |

As on the synthetic corpus, no model separates no-answer questions by score. Rejecting an unknown name costs between 13% and 35% of the real questions, depending on the model. A name that is not in the data is better caught by an exact check against the list of student names than by a similarity threshold.

### What the real data shows

- **BGE-M3 and Arctic are tied, and both are clearly ahead of the rest at rank 1.** Arctic leads by one question at rank 1; BGE-M3 leads by four in the top 3 and by one in the top 5.
- **bge-small-en is close behind at a tenth of the memory.** It trails BGE-M3 by two questions at rank 1 and one in the top 5. Its weak spot is paraphrased questions (4 of 10 at rank 1 against 7 of 10).
- **GTE-ModernBERT fails on this data.** It is below keyword search overall, found none of the ten sheet-description cards in its top 10, and got 3 of 10 short "name plus sheet" queries. It is not suitable for these spreadsheets.
- **Keyword search is strong where names decide.** TF-IDF matches the best model in the top 5 (58 of 60) and is weak only at rank 1, where near-duplicate rows of the same student confuse it (4 of 10 on similar-document questions). The two approaches fail on different questions, which is the case for combining them.
- **One question (R044, technical) was missed by every model, including keyword search.** That points to the question or the sheet card, not the models: most likely the student rows of a large sheet outrank its own description card. It does not affect the ranking.
- **Timing is now consistent.** BGE-M3 and Arctic have the same latency, throughput and memory. Chunks here average 90 tokens, so throughput is lower than on the synthetic corpus.

### Limits of this test

- Questions were generated from templates built on the data, so they test finding a named student in a named sheet. They do not represent how staff will phrase real requests.
- Sixty questions separate strong models from weak ones but cannot rank BGE-M3 against Arctic.
- Counting and ranking questions are absent because retrieval cannot answer them.
- One attendance file was not read.

## 7. Recommendation and decision rules

**Primary: BGE-M3. Backup: bge-small-en-v1.5.** Based on the real-data results in section 6, which outrank the synthetic results in `embedding_benchmark.md`.

- **BGE-M3 over Arctic** is a tie-break between two models that measure the same. BGE-M3 has the better top-3 recall and MRR, handles sheet-description questions better (8 of 10 against 6 of 10), and brings three further advantages: sparse output for hybrid search from the same model, the MIT licence, and evidence on Khmer, where a May 2026 study (200 questions, 7,000+ chunks) found it ahead of Qwen3-Embedding on every metric. The data is English today, but student names and any future Khmer text make this relevant for an HRD centre in Cambodia. Arctic's Khmer quality is untested. Arctic is a sound substitute if any of those stop mattering.
- **bge-small-en as backup** because a backup should be cheaper to run, not a second model of the same size. It gives up two questions at rank 1 for a tenth of the VRAM.
- **GTE-ModernBERT is dropped.** Its synthetic result did not carry over.
- **Qwen3-0.6B and Granite English R2** were not re-tested on real data. Neither led on the synthetic test, and Granite shares GTE-ModernBERT's architecture and size, so it should be re-tested before being trusted on this data.

Recommended system design for this data, beyond the choice of model:

1. **Hybrid retrieval.** Combine keyword search with the embedding model. Names are exact tokens, and the two methods miss different questions.
2. **Structured queries for calculations.** Route counting, ranking and averaging questions to a query over the tables, with retrieval used to pick the right sheet.
3. **Exact name check for refusals.** Detect "no such student" by looking the name up, not by a similarity threshold.

What would change the picks:

1. A set of 50 or more questions written by the mentors or staff, in their own wording. Rank by Recall@5, then MRR@10; treat a gap of one or two questions as a tie.
2. If Arctic beats BGE-M3 by three or more questions on that set, switch.
3. If bge-small-en stays within two questions of the primary on that set, and no Khmer text is planned, it becomes the better engineering choice outright.
4. If Khmer-script names or documents are added, re-test: bge-small-en is English-only and would be expected to fail.
5. Test hybrid search (BGE-M3 dense plus sparse, or dense plus BM25). If it lifts Recall@1 noticeably, the hybrid setup matters more than which dense model is used.

## 8. Configuration

```yaml
embedding:
  primary:
    model: BAAI/bge-m3
    revision: <pin the commit hash you benchmarked>
    dtype: float16 # GPU; float32 on CPU
    dimensions: 1024
    max_seq_length: 512
    batch_size: 16
    normalize: true
    similarity: cosine
    query_prompt: none
    document_prompt: none
    sparse: optional # BGE-M3 lexical weights, for hybrid search (untested here)
  backup:
    model: BAAI/bge-small-en-v1.5
    revision: <pin the commit hash you benchmarked>
    dtype: float16
    dimensions: 384
    max_seq_length: 512
    batch_size: 16
    normalize: true
    similarity: cosine
    query_prompt: none # as benchmarked; its optional query instruction was not used
    document_prompt: none
chunking: # for the Excel workbooks
  unit: one chunk per student row, plus one description card per sheet
  row_text: "<Column>: <value>; <Column>: <value>; ..." # empty cells left out
  card_text: sheet title lines, row count, column names, footer notes
  prefix: "<workbook name> - <sheet name>\n"
retrieval:
  top_k: 5 # right row in the top 5 for 58 of 60 questions with the primary
  hybrid: recommended # add keyword search; see section 7
  no_answer: exact name lookup or a check after retrieval, not a score threshold
runtime:
  HF_HUB_OFFLINE: 1 # after the first download; nothing leaves the machine
```

- Measured with the primary on real data: 15 ms per query, about 250 chunks per second, 1.2 GB VRAM, 3.0 GB RAM. With the backup: 9 ms, about 1,180 chunks per second, 109 MB VRAM, 1.5 GB RAM.
- The two models produce different vector sizes (1024 vs 384). Switching to the backup means re-embedding everything into a separate index. With about 400 chunks that takes seconds, so keeping both indexes built costs nothing.
- Changing the model, its revision or the chunk text format also requires re-embedding.
- The workbook name and sheet name are placed in front of every chunk. Keep that in production, since the measured results depend on it and it is what lets a question name a sheet.
- For free-text documents added later, use chunks of 300-400 tokens with 50 overlap, split on headings, and re-run the benchmark; nothing in this report measures that case on real data.

## 9. Files

Paths are relative to the project root.

- `real_data/embedding_benchmark_real_data.md`: this report.
- `synthetic/embedding_benchmark.md`: the earlier report on the synthetic corpus, with candidate research and specifications.
- `benchmark.py`: the benchmark, shared by both reports; one process per model.
- `real_data/excel_to_corpus.py`: reads the Excel workbooks in place and writes the corpus and questions.
- `real_data/inspect_layout.py`: prints the layout of Excel sheets with every cell masked, for checking new files.
- `real_data/docs/`: the HRD workbooks. Confidential; excluded from git.
- `real_data/real/`: generated `corpus.jsonl` and `queries.jsonl`. They contain student names and scores; excluded from git.
- `real_data/results_real/`: output of the benchmark runs; excluded from git.

To reproduce, from the project root:

```
python3 real_data/excel_to_corpus.py real_data/docs --out real_data/real
python3 benchmark.py --corpus real_data/real/corpus.jsonl --queries real_data/real/queries.jsonl --out real_data/results_real --models tfidf-baseline bge-small-en gte-modernbert arctic-l-v2 bge-m3
```

## Sources

- [BAAI/bge-m3 model card](https://huggingface.co/BAAI/bge-m3)
- [BAAI/bge-small-en-v1.5 model card](https://huggingface.co/BAAI/bge-small-en-v1.5)
- [Snowflake/snowflake-arctic-embed-l-v2.0 model card](https://huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0)
- [Alibaba-NLP/gte-modernbert-base model card](https://huggingface.co/Alibaba-NLP/gte-modernbert-base)
- [A Comparative Study of Language Models for Khmer Retrieval-Augmented Question Answering (arXiv 2605.22099)](https://arxiv.org/abs/2605.22099)
