# Embedding Model Benchmark

Owner: Panha · Date: 2026-10-06 · Status: **measured on the RTX 3060 with a synthetic corpus; confirmation on real HRD documents pending**

## 1. Bottom line

| Role        | Model                                     | Why                                                                                                                                                                                                                                                |
| ----------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Primary** | `Snowflake/snowflake-arctic-embed-l-v2.0` | The only model to put the right chunk first for all 13 answerable questions (Recall@1 1.000). 14 ms per query, 1.1 GB VRAM, Apache 2.0, not gated.                                                                                                 |
| **Backup**  | `Alibaba-NLP/gte-modernbert-base`         | 12 of 13 at rank 1 and every answer in the top 3, at a quarter of the VRAM (332 MB) and the highest throughput of any model tested. English-only like the corpus, Apache 2.0, no query prompt.                                                     |
| BGE-M3      | Not selected                              | Tied with the backup on quality (12 of 13 at rank 1) but slower per query and the heaviest on RAM. Arctic is the same size and scored higher on every measure. BGE-M3 remains the model to re-test first if Khmer documents are added (section 4). |

**How firm this is.** Five candidates and two popular reference models were measured on the target GPU, so speed and memory figures are real. The quality ranking is weak: the test set has 13 answerable questions over a synthetic 42-chunk corpus, and the models differ by one or two questions. The clearest sign is that `all-MiniLM-L6-v2`, a 2021 model with about 23M parameters, scored 12 of 13 at rank 1, level with BGE-M3 and Qwen3, using 64 MB of VRAM. **This test is too easy to show whether a larger model is worth its cost.** The picks are the best reading of the evidence so far; a harder test on real documents could change them, including in favour of a much smaller model. Section 8 says what would change them.

**The query set is a stand-in.** The real HRD documents are confidential and were not shared, so the 16 questions in section 5 run against a synthetic HR corpus written for this benchmark. Re-running on real documents with 50 or more questions is the remaining step.

**Changes from the first draft.** Qwen3-Embedding-0.6B and Granite English R2 were the picks on paper. Measurement moved both down: Qwen3 had no quality advantage and was the slowest to index, and Granite was matched in cost and beaten by one question by GTE-ModernBERT. EmbeddingGemma and Jina v5 could not be run and were replaced by Arctic and GTE-ModernBERT (section 3).

## 2. Constraints

- Documents and queries: English only.
- Hardware: RTX 3060 with 6-8 GB VRAM, run under WSL.
- Documents are confidential, so the model must run fully offline.
- Open question: if the answer-generating LLM shares this GPU, the embedding model's VRAM comes out of the LLM's budget. That favours the backup (332 MB against 1,123 MB).

## 3. Candidates

### Measured

|                                      | Arctic Embed L v2.0                       | GTE-ModernBERT-base                              | BGE-M3                               | Qwen3-Embedding-0.6B        | Granite-Embedding-English-R2               |
| ------------------------------------ | ----------------------------------------- | ------------------------------------------------ | ------------------------------------ | --------------------------- | ------------------------------------------ |
| Hugging Face id                      | `Snowflake/snowflake-arctic-embed-l-v2.0` | `Alibaba-NLP/gte-modernbert-base`                | `BAAI/bge-m3`                        | `Qwen/Qwen3-Embedding-0.6B` | `ibm-granite/granite-embedding-english-r2` |
| Parameters                           | 568M                                      | 149M                                             | ~568M                                | 0.6B                        | 149M                                       |
| Dimensions                           | 1024 (truncatable to 256)                 | 768                                              | 1024                                 | 1024 (truncatable 32-1024)  | 768                                        |
| Max input (tokens)                   | 8,192                                     | 8,192                                            | 8,192                                | 32,000                      | 8,192                                      |
| Languages                            | 74                                        | English only                                     | 100+                                 | 100+                        | English only                               |
| Licence                              | Apache 2.0                                | Apache 2.0                                       | MIT                                  | Apache 2.0                  | Apache 2.0                                 |
| Gated download                       | No                                        | No                                               | No                                   | No                          | No                                         |
| Query prompt needed                  | Yes (built into the model)                | No                                               | No                                   | Yes (instruction)           | No                                         |
| Peak VRAM, measured (fp16, batch 16) | 1,123 MB                                  | 332 MB                                           | 1,123 MB                             | 1,318 MB                    | 331 MB                                     |
| Peak RAM, measured                   | 2.9 GB                                    | 1.6 GB                                           | 3.5 GB                               | 2.0 GB                      | 1.8 GB                                     |
| Notes                                | Published BEIR 55.6                       | Published BEIR 55.33; needs `transformers>=4.48` | Also outputs sparse and multi-vector | Left padding required       | ModernBERT encoder                         |

All five fit a 6 GB card with room to spare. VRAM was measured on short chunks (about 55 tokens); chunks of 300-400 tokens will use more.

### Selected originally but not run

| Model                                  | Reason                                                                                                                                                                                       |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `google/embeddinggemma-300m`           | Gated under Google's Gemma terms. The download was refused ("requires approval") after login, and access was not granted during testing. 300M parameters, 768 dimensions, 2,048-token limit. |
| `jinaai/jina-embeddings-v5-text-small` | CC BY-NC 4.0, non-commercial use only, and it needs newer libraries (`transformers>=5.1`, `peft`). Not attempted.                                                                            |

Both entries are still in `benchmark.py` and can be run later if access or licensing is resolved.

### Considered and left out

- **Qwen3-Embedding-4B**: stronger on paper (MTEB English v2 retrieval 68.46 against 61.83 for the 0.6B), but about 8 GB in fp16 by a parameters × 2 bytes estimate, so it does not fit this card without quantisation.
- **multilingual-e5-large-instruct**: 53.47 on English v2 retrieval in Qwen's comparison table, well below Qwen3-0.6B.

## 4. Why BGE-M3 is not the automatic choice

- Measured here, BGE-M3 was good: 12 of 13 at rank 1, every answer in the top 3, and the best MRR after Arctic. It is not a bad choice.
- Arctic is the same size, used the same VRAM, and did better on every measure in this run: one more question at rank 1, 14 ms against 36 ms per query, 407 against 268 chunks per second, and 2.9 GB against 3.5 GB of RAM.
- BGE-M3's distinctive advantages do not apply yet: broad multilingual coverage, and sparse output for hybrid search.
- Evidence in its favour for a different corpus: a May 2026 study of Khmer retrieval (200 questions, 7,000+ chunks) found BGE-M3 ahead of Qwen3-Embedding on every metric (Hit Rate@5 0.355 vs 0.205, MRR@3 0.221 vs 0.141). **If Khmer documents or Khmer questions enter scope, re-run the benchmark with BGE-M3 included.** Arctic's Khmer quality is untested here.

## 5. HRD retrieval questions

16 questions over a synthetic corpus of 8 documents and 42 chunks (`corpus.jsonl`, `queries.jsonl`). Every fact in the corpus is invented. Chunk ids read `document#section#chunk`.

| ID  | Type             | Query                                                                                                                                                                                                                                                 | Expected document                                       | Section                                                              | Chunk                                            |
| --- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------ |
| Q01 | Exact            | What is the maximum number of unused annual leave days that may be carried over to the next year?                                                                                                                                                     | HRD-POL-001 Annual Leave Policy                         | 4 Carry-over and Payout                                              | `HRD-POL-001#s4#c01`                             |
| Q02 | Exact            | After how many failed login attempts is the account locked, and for how long?                                                                                                                                                                         | HRD-IT-007 HRIS Access and Password Standard            | 2 Password Requirements                                              | `HRD-IT-007#s2#c01`                              |
| Q03 | Paraphrased      | I've been ill for three days in a row. Do I have to bring a doctor's note?                                                                                                                                                                            | HRD-POL-002 Sick and Special Leave Policy               | 2 Sick Leave Entitlement                                             | `HRD-POL-002#s2#c01`                             |
| Q04 | Paraphrased      | Can I challenge my appraisal score if I think it is unfair?                                                                                                                                                                                           | HRD-PRO-004 Performance Review Procedure                | 4 Calibration and Appeals                                            | `HRD-PRO-004#s4#c01`                             |
| Q05 | Short            | overtime rate Sunday                                                                                                                                                                                                                                  | HRD-POL-008 Remote Work and Attendance Policy           | 4 Overtime                                                           | `HRD-POL-008#s4#c01`                             |
| Q06 | Short            | training bond                                                                                                                                                                                                                                         | HRD-POL-003 Training and Development Policy             | 4 Training Bond                                                      | `HRD-POL-003#s4#c01`                             |
| Q07 | Long             | I joined six weeks ago and I am still on probation. My sister is getting married abroad next month and I would like to take a full week off to attend. Am I allowed to use my annual leave already, or do I have to wait until I have been confirmed? | HRD-HB-005 Staff Onboarding and Probation Handbook      | 4 Benefits During Probation                                          | `HRD-HB-005#s4#c01`                              |
| Q08 | Long             | My manager wants me to attend a three-day cloud certification course that costs 1,900 dollars and starts in about a month. What do I need to submit, who has to sign off given the cost, and would I owe anything back if I resign next year?         | HRD-POL-003 Training and Development Policy             | 4 Training Bond (also 3 Approval Workflow, 2 Annual Training Budget) | `HRD-POL-003#s4#c01` (also `#s3#c01`, `#s2#c01`) |
| Q09 | Technical        | HRIS API token expiry and rate limit for service accounts                                                                                                                                                                                             | HRD-IT-007 HRIS Access and Password Standard            | 4 API Tokens                                                         | `HRD-IT-007#s4#c01`                              |
| Q10 | Technical        | Is SMS OTP accepted for MFA, or only TOTP with SAML SSO?                                                                                                                                                                                              | HRD-IT-007 HRIS Access and Password Standard            | 1 Authentication                                                     | `HRD-IT-007#s1#c01`                              |
| Q11 | Similar-document | How long does an internship last and can it be extended?                                                                                                                                                                                              | HRD-HB-006 Intern Handbook                              | 1 Internship Duration                                                | `HRD-HB-006#s1#c01`                              |
| Q12 | Similar-document | Do unused sick days roll over to the next year?                                                                                                                                                                                                       | HRD-POL-002 Sick and Special Leave Policy               | 5 Carry-over                                                         | `HRD-POL-002#s5#c01`                             |
| Q13 | Similar-document | Can the probation period for new staff be extended, and by how much?                                                                                                                                                                                  | HRD-HB-005 Staff Onboarding and Probation Handbook      | 2 Probation Period                                                   | `HRD-HB-005#s2#c01`                              |
| Q14 | No-answer        | What is the policy on stock options and equity vesting?                                                                                                                                                                                               | none                                                    | -                                                                    | -                                                |
| Q15 | No-answer        | How many annual leave days do contractors in the Singapore office get?                                                                                                                                                                                | none (near miss: leave is covered, contractors are not) | -                                                                    | -                                                |
| Q16 | No-answer        | What is the dress code for client meetings?                                                                                                                                                                                                           | none                                                    | -                                                                    | -                                                |

The similar-document questions each have a deliberate trap: Q11 and Q13 mirror each other (internship extension vs probation extension), and Q12 mirrors Q01 (sick leave vs annual leave carry-over). Q07 mentions a wedding, which pulls towards the special-leave chunk.

## 6. Method

- **Recall@k** (k = 1, 3, 5): share of answerable questions with an expected chunk in the top k. For Q08, any of its three chunks counts.
- **MRR@10**: mean of 1 / rank of the first expected chunk; 0 if outside the top 10.
- **Doc@1**: share of questions whose top result is from the right document, even if the wrong chunk.
- **No-answer**: these questions are excluded from recall and MRR. The script compares top-1 similarity for answerable and no-answer questions and reports the threshold that best separates them.
- **Latency**: time to embed one query and search, 5 repeats per query after warm-up; p50 and p95.
- **Chunks/sec**: time to embed 2,000 chunks (the corpus repeated) at batch size 16.
- **RAM / VRAM**: peak process memory and peak CUDA memory allocated, one process per model.
- Settings: cosine similarity on normalised vectors, `max_seq_length` 512, chunk text prefixed with document title and section, fp16 on the GPU.
- Each model was run once, across four separate invocations of the script. Timing figures can vary between runs.

## 7. Results

Measured on the RTX 3060 under WSL, 2026-10-06. 13 answerable questions, 3 no-answer questions, 42 chunks.

### Summary

| Model                               | R@1                                | R@3   | R@5   | MRR@10    | Doc@1 | Query p50 / p95 ms | Chunks/s | Peak RAM MB | Peak VRAM MB |
| ----------------------------------- | ---------------------------------- | ----- | ----- | --------- | ----- | ------------------ | -------- | ----------- | ------------ |
| **Arctic Embed L v2.0**             | **1.000**                          | 1.000 | 1.000 | **1.000** | 1.000 | 14.2 / 22.2        | 407.3    | 2,867       | 1,123        |
| BGE-M3                              | 0.923                              | 1.000 | 1.000 | 0.962     | 1.000 | 36.3 / 72.6        | 268.3    | 3,546       | 1,123        |
| **GTE-ModernBERT-base**             | 0.923                              | 1.000 | 1.000 | 0.949     | 1.000 | 13.2 / 19.8        | 592.6    | 1,554       | 332          |
| Qwen3-Embedding-0.6B                | 0.923                              | 1.000 | 1.000 | 0.949     | 0.923 | 28.4 / 31.4        | 195.7    | 2,041       | 1,318        |
| Granite-Embedding-English-R2        | 0.846                              | 0.923 | 1.000 | 0.900     | 0.923 | 15.2 / 21.5        | 522.9    | 1,799       | 331          |
| TF-IDF baseline (lexical reference) | 0.615                              | 0.769 | 0.846 | 0.710     | 0.692 | n/a                | n/a      | n/a         | 0            |
| _Reference:_ all-MiniLM-L6-v2       | 0.923                              | 1.000 | 1.000 | 0.962     | 1.000 | 4.3 / 5.2          | 2,048.8  | 1,516       | 64           |
| _Reference:_ bge-small-en-v1.5      | 0.923                              | 0.923 | 1.000 | 0.938     | 0.923 | 7.4 / 8.3          | 1,524.1  | 1,558       | 86           |
| EmbeddingGemma-300M                 | not run: gated, access not granted |       |       |           |       |                    |          |             |              |
| Jina-Embeddings-v5-text-small       | not run: non-commercial licence    |       |       |           |       |                    |          |             |              |

The two reference rows are the most downloaded embedding models on Hugging Face (253M and 71M downloads), added to check the candidates against what most people use. Both produce 384-dimension vectors. They are not candidates: all-MiniLM-L6-v2 is designed for inputs up to 256 tokens, shorter than the planned 300-400 token chunks, and bge-small-en-v1.5 is limited to 512.

Chunks/s was measured on chunks averaging 52-58 tokens. Real chunks of 300-400 tokens will be several times slower for every model.

### Rank of the first expected chunk, per question

| Model                          | Q01 | Q02 | Q03           | Q04 | Q05 | Q06 | Q07   | Q08 | Q09 | Q10 | Q11 | Q12   | Q13 |
| ------------------------------ | --- | --- | ------------- | --- | --- | --- | ----- | --- | --- | --- | --- | ----- | --- |
| Arctic Embed L v2.0            | 1   | 1   | 1             | 1   | 1   | 1   | 1     | 1   | 1   | 1   | 1   | 1     | 1   |
| BGE-M3                         | 1   | 1   | **2**         | 1   | 1   | 1   | 1     | 1   | 1   | 1   | 1   | 1     | 1   |
| GTE-ModernBERT-base            | 1   | 1   | **3**         | 1   | 1   | 1   | 1     | 1   | 1   | 1   | 1   | 1     | 1   |
| Qwen3-Embedding-0.6B           | 1   | 1   | 1             | 1   | 1   | 1   | **3** | 1   | 1   | 1   | 1   | 1     | 1   |
| Granite-Embedding-English-R2   | 1   | 1   | **2**         | 1   | 1   | 1   | **5** | 1   | 1   | 1   | 1   | 1     | 1   |
| _Reference:_ all-MiniLM-L6-v2  | 1   | 1   | 1             | 1   | 1   | 1   | 1     | 1   | 1   | 1   | 1   | **2** | 1   |
| _Reference:_ bge-small-en-v1.5 | 1   | 1   | 1             | 1   | 1   | 1   | **5** | 1   | 1   | 1   | 1   | 1     | 1   |
| TF-IDF baseline                | 1   | 1   | not in top 10 | 4   | 1   | 1   | 3     | 7   | 1   | 1   | 1   | 2     | 1   |

Only two questions separate the five candidates: Q03 (the "doctor's note" paraphrase) and Q07 (the long probation question with a wedding as a distraction). Every candidate got all exact, short, technical and similar-document questions right at rank 1. all-MiniLM-L6-v2 was the only neural model to fall for a similar-document trap (Q12, sick leave vs annual leave carry-over).

### Recall@1 / MRR@10 by query type

| Model                          | Exact       | Paraphrased | Short       | Long        | Technical   | Similar-document |
| ------------------------------ | ----------- | ----------- | ----------- | ----------- | ----------- | ---------------- |
| Arctic Embed L v2.0            | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00      |
| BGE-M3                         | 1.00 / 1.00 | 0.50 / 0.75 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00      |
| GTE-ModernBERT-base            | 1.00 / 1.00 | 0.50 / 0.67 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00      |
| Qwen3-Embedding-0.6B           | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.50 / 0.67 | 1.00 / 1.00 | 1.00 / 1.00      |
| Granite-Embedding-English-R2   | 1.00 / 1.00 | 0.50 / 0.75 | 1.00 / 1.00 | 0.50 / 0.60 | 1.00 / 1.00 | 1.00 / 1.00      |
| _Reference:_ all-MiniLM-L6-v2  | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.67 / 0.83      |
| _Reference:_ bge-small-en-v1.5 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.50 / 0.60 | 1.00 / 1.00 | 1.00 / 1.00      |
| TF-IDF baseline                | 1.00 / 1.00 | 0.00 / 0.12 | 1.00 / 1.00 | 0.00 / 0.24 | 1.00 / 1.00 | 0.67 / 0.83      |

### No-answer questions

| Model                          | Mean top-1 score (answerable) | Lowest top-1 (answerable) | Highest top-1 (no-answer) | Best threshold | No-answer rejected | Answerable kept |
| ------------------------------ | ----------------------------- | ------------------------- | ------------------------- | -------------- | ------------------ | --------------- |
| Arctic Embed L v2.0            | 0.565                         | 0.304                     | 0.491                     | 0.280          | 2 of 3             | 13 of 13        |
| BGE-M3                         | 0.665                         | 0.566                     | 0.596                     | 0.531          | 2 of 3             | 13 of 13        |
| GTE-ModernBERT-base            | 0.764                         | 0.641                     | 0.729                     | 0.619          | 2 of 3             | 13 of 13        |
| Qwen3-Embedding-0.6B           | 0.681                         | 0.479                     | 0.596                     | 0.618          | 3 of 3             | 9 of 13         |
| Granite-Embedding-English-R2   | 0.883                         | 0.831                     | 0.885                     | 0.815          | 2 of 3             | 13 of 13        |
| _Reference:_ all-MiniLM-L6-v2  | 0.619                         | 0.369                     | 0.594                     | 0.332          | 2 of 3             | 13 of 13        |
| _Reference:_ bge-small-en-v1.5 | 0.784                         | 0.640                     | 0.753                     | 0.623          | 2 of 3             | 13 of 13        |

**No model can detect a no-answer question from the similarity score alone.** In every model at least one no-answer question scores higher than a real match. Six models let one no-answer question through; Qwen3 rejects all three only by also discarding 4 of the 13 real questions. Refusing to answer has to be handled after retrieval, by a reranker or by the LLM checking that the retrieved text contains the answer.

### What the results do and do not show

- Embedding models are clearly worth it over keyword search: the TF-IDF baseline failed every paraphrased and long question at rank 1.
- The neural models are close. One question is worth 7.7 points of Recall@1, so Arctic's lead over BGE-M3, GTE-ModernBERT and Qwen3 is a single question.
- The test does not discriminate by model size. The two small reference models (64 and 86 MB of VRAM) each missed one question at rank 1, the same as three of the five candidates. The likely reasons are the small corpus, short chunks on clearly different topics, and the title and section prefix on every chunk, which hands the model the topic. A larger corpus with longer and more similar chunks is needed before paying for a 568M model can be justified by data.
- Cost differences are large and reliable: the two 149M models use about 330 MB of VRAM against 1.1-1.3 GB for the others.
- Qwen3 had the lowest indexing throughput (196 chunks/s) and the highest VRAM, with no quality advantage to pay for it.

## 8. Recommendation and decision rules

**Primary: Arctic Embed L v2.0. Backup: GTE-ModernBERT-base.**

- **Arctic** is first or tied for first on every quality measure, is as fast per query as the small models, and has a permissive licence and an open download. Its lead is one question, so it is the best-supported choice, not a proven winner.
- **GTE-ModernBERT** is the backup because it is a different size class: if VRAM gets tight when an LLM shares the GPU, it gives nearly the same retrieval for under a third of the memory. It beat Granite, its direct rival, by one question at the same cost.
- **BGE-M3**: see section 4.
- **Qwen3-0.6B** and **Granite English R2** are usable but offered nothing the two picks do not.

Confirm on real HRD documents with 50 or more questions, keeping the seven query types:

1. Rank by Recall@5, then MRR@10. Treat a gap of one or two questions as a tie.
2. Keep Arctic as primary if it is best or tied for best.
3. If GTE-ModernBERT ties Arctic on real data, prefer it when the GPU is shared with an LLM, since it is smaller and faster.
4. If another model wins by a clear margin (three or more questions out of 50), take the winner.
5. If every model misses the same exact-term questions (form codes, policy ids), add keyword search alongside the embedding model before changing models.
6. Include a small model in the real-data run (bge-small-en-v1.5, or all-MiniLM-L6-v2 if chunks stay under 256 tokens). If it stays within a question or two of Arctic on 50 or more real questions, the small model is the better engineering choice.
7. Re-measure chunks/sec and VRAM with real chunk lengths before sizing the indexing job.

## 9. Configuration

```yaml
embedding:
  primary:
    model: Snowflake/snowflake-arctic-embed-l-v2.0
    revision: <pin the commit hash you benchmarked>
    dtype: float16 # GPU; float32 on CPU
    dimensions: 1024 # full size; corpus is small, no need to truncate
    max_seq_length: 512
    batch_size: 16
    normalize: true
    similarity: cosine
    query_prompt: prompt_name="query" # built into the model; queries only
    document_prompt: none
  backup:
    model: Alibaba-NLP/gte-modernbert-base
    revision: <pin the commit hash you benchmarked>
    dtype: float16
    dimensions: 768
    max_seq_length: 512
    batch_size: 16
    normalize: true
    similarity: cosine
    query_prompt: none
    document_prompt: none
chunking:
  size_tokens: 300-400
  overlap_tokens: 50
  split_on: section headings first, then paragraphs
  prefix: "<document title> - <section heading>\n"
retrieval:
  top_k: 5 # every model had the answer in the top 5; Arctic in the top 1
  no_answer: handled after retrieval (reranker or LLM check), not by a score threshold
runtime:
  HF_HUB_OFFLINE: 1 # after the first download; nothing leaves the machine
```

- Arctic needs its query prompt on queries and nothing on documents. Leaving the prompt off queries will lower recall.
- The two models produce different vector sizes (1024 vs 768). Switching to the backup means re-embedding the whole corpus into a separate index; keep both indexes built if fast failover matters.
- Changing the model, its revision, the query prompt or the chunk prefix also requires re-embedding.
- The benchmark embedded each chunk with its document title and section heading in front. Keep that prefix in production, since the measured results depend on it.

## 10. Files

- `embedding-benchmark.md`: this report.
- `benchmark.py`: the benchmark; one process per model, writes `results/results.md`. Model keys: `arctic-l-v2`, `gte-modernbert`, `bge-m3`, `qwen3-0.6b`, `granite-en-r2`, `tfidf-baseline`, the reference models `minilm-l6` and `bge-small-en`, plus `embeddinggemma` and `jina-v5-small` (not run).
- `make_dataset.py`: generates the synthetic `corpus.jsonl` and `queries.jsonl`. For real data, write those two files directly with the same fields (`chunk_id`, `doc_id`, `doc_title`, `section`, `text`; `query_id`, `type`, `query`, `expected_chunks`).

To reproduce the full table in one run:

```
python3 benchmark.py --models tfidf-baseline granite-en-r2 qwen3-0.6b bge-m3 gte-modernbert arctic-l-v2
```

## Sources

- [Snowflake/snowflake-arctic-embed-l-v2.0 model card](https://huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0)
- [Alibaba-NLP/gte-modernbert-base model card](https://huggingface.co/Alibaba-NLP/gte-modernbert-base)
- [BAAI/bge-m3 model card](https://huggingface.co/BAAI/bge-m3)
- [Qwen/Qwen3-Embedding-0.6B model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
- [ibm-granite/granite-embedding-english-r2 model card](https://huggingface.co/ibm-granite/granite-embedding-english-r2)
- [google/embeddinggemma-300m model card](https://huggingface.co/google/embeddinggemma-300m)
- [jinaai/jina-embeddings-v5-text-small model card](https://huggingface.co/jinaai/jina-embeddings-v5-text-small)
- [Hugging Face model API, sorted by downloads](https://huggingface.co/api/models?pipeline_tag=sentence-similarity&sort=downloads&direction=-1&limit=25) (popularity figures, 2026-10-06)
- [A Comparative Study of Language Models for Khmer Retrieval-Augmented Question Answering (arXiv 2605.22099)](https://arxiv.org/abs/2605.22099)
