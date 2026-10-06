# Embedding Model Benchmark

Owner: Panha · Date: 2026-10-06 · Status: **selection provisional, measurements pending on the RTX 3060**

## 1. Bottom line

| Role                      | Model                                      | Why                                                                                                                                                                                                                 |
| ------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Primary (provisional)** | `Qwen/Qwen3-Embedding-0.6B`                | Best published English retrieval score among the candidates with a commercial-friendly licence (MTEB English v2 retrieval 61.83), Apache 2.0, about 1.2 GB of weights in fp16.                                      |
| **Backup (provisional)**  | `ibm-granite/granite-embedding-english-r2` | English-only like the corpus, 149M parameters (about a quarter the size), Apache 2.0, no query prompt to get wrong. The fallback if Qwen3 is too slow or too heavy next to the LLM on the same GPU.                 |
| BGE-M3                    | Not selected for this corpus               | Its strengths are multilingual and hybrid (dense + sparse) retrieval. The corpus is English-only, and BGE-M3 is larger than both picks. It becomes the first choice again if Khmer documents are added (section 4). |

**What is and is not measured.** The five candidates could not be run where this report was written: model downloads were blocked there and it had no GPU. The picks above therefore rest on published specifications and vendor-reported scores, not on Recall@k measured on HRD data. Section 7 has the results table with one measured row (a TF-IDF baseline) and the candidate rows empty. Running `benchmark.py` on the RTX 3060 fills them in, and section 8 gives the rules for confirming or changing the picks.

**The query set is a stand-in.** The real HRD documents are confidential and were not shared, so the 16 questions in section 5 run against a synthetic 42-chunk HR corpus written for this benchmark. The questions must be rewritten against the real documents before the numbers decide anything.

## 2. Constraints

- Documents and queries: English only.
- Hardware: RTX 3060 with 6-8 GB VRAM. Plan for 6 GB.
- Documents are confidential, so the model must run fully offline.
- Open question: if the answer-generating LLM shares this GPU, the embedding model's VRAM comes out of the LLM's budget. That favours the smaller backup, or running embeddings on CPU.

## 3. Candidates

|                                 | BGE-M3                               | Qwen3-Embedding-0.6B        | EmbeddingGemma-300M                  | Granite-Embedding-English-R2               | Jina-Embeddings-v5-text-small          |
| ------------------------------- | ------------------------------------ | --------------------------- | ------------------------------------ | ------------------------------------------ | -------------------------------------- |
| Hugging Face id                 | `BAAI/bge-m3`                        | `Qwen/Qwen3-Embedding-0.6B` | `google/embeddinggemma-300m`         | `ibm-granite/granite-embedding-english-r2` | `jinaai/jina-embeddings-v5-text-small` |
| Parameters                      | ~568M                                | 0.6B                        | 300M                                 | 149M                                       | 677M                                   |
| Dimensions                      | 1024                                 | 1024 (truncatable 32-1024)  | 768 (512 / 256 / 128)                | 768                                        | 1024 (truncatable 32-1024)             |
| Max input (tokens)              | 8,192                                | 32,000                      | 2,048                                | 8,192                                      | 32,768                                 |
| Languages                       | 100+                                 | 100+                        | 100+                                 | English only                               | 119+                                   |
| Licence                         | MIT                                  | Apache 2.0                  | Gemma terms, gated download          | Apache 2.0                                 | **CC BY-NC 4.0** (non-commercial)      |
| Weights in VRAM (GPU precision) | 1.06 GB fp16                         | ~1.2 GB fp16 \*             | ~0.6 GB bf16 \*                      | ~0.3 GB fp16 \*                            | ~1.35 GB bf16 \*                       |
| Fits 6 GB VRAM                  | Yes                                  | Yes                         | Yes                                  | Yes                                        | Yes                                    |
| Query prompt needed             | No                                   | Yes (instruction)           | Yes (query and document)             | No                                         | Yes (query and document)               |
| Notes                           | Also outputs sparse and multi-vector | Left padding required       | No float16; needs Hugging Face login | ModernBERT encoder, Aug 2025               | Needs `transformers>=5.1`, `peft`      |

\* Estimated as parameters × bytes per weight; not a vendor figure. BGE-M3's 1.06 GB is from its model page. Working VRAM during encoding is higher (batch size × sequence length) and is one of the things the benchmark measures.

### Published English scores (vendor-reported)

| Model                | Figure                                                                                          | Source            |
| -------------------- | ----------------------------------------------------------------------------------------------- | ----------------- |
| Qwen3-Embedding-0.6B | MTEB English v2: mean 70.70, **retrieval 61.83**                                                | Qwen model card   |
| Jina v5 text-small   | MTEB English v2: mean 71.7                                                                      | Jina model card   |
| EmbeddingGemma-300M  | MTEB English v2: mean 69.67 (retrieval not broken out)                                          | Google model card |
| Granite English R2   | 59.5 average on IBM's own retrieval suite, ahead of gte-modernbert-base (57.5) at the same size | IBM model card    |
| BGE-M3               | No English v2 figure on its card                                                                | -                 |

These figures are on different bases and cannot be ranked against each other directly: Granite's number is IBM's own average, and the "mean" scores include classification and clustering tasks that do not matter for retrieval. That is why the local benchmark is the deciding step.

### Considered and left out

- **Qwen3-Embedding-4B**: clearly stronger on paper (English v2 retrieval 68.46), but about 8 GB in fp16 by the same estimate, so it does not fit 6 GB without quantisation. Worth a test in a quantised build only if the 0.6B model's recall is not good enough.
- **multilingual-e5-large-instruct**: 53.47 on English v2 retrieval in Qwen's comparison table, well below Qwen3-0.6B.
- **gte-modernbert-base**: same size as Granite English R2 and behind it in IBM's table.
- **snowflake-arctic-embed-l-v2.0**: multilingual model; its page could not be opened during research, so its specs are unverified here.

## 4. Why BGE-M3 is not the automatic choice

- For English-only text there is no published evidence that BGE-M3 beats the newer models, and it is larger than both picks.
- Its real advantages do not apply yet: multilingual coverage, and sparse output for hybrid search.
- Evidence in its favour for a different corpus: a May 2026 study of Khmer retrieval (200 questions, 7,000+ chunks) found BGE-M3 ahead of Qwen3-Embedding on every metric (Hit Rate@5 0.355 vs 0.205, MRR@3 0.221 vs 0.141). **If Khmer documents or Khmer questions enter scope, re-run the benchmark with BGE-M3 as the expected primary.**

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

**Before trusting results:** rewrite these against the real documents, keep the seven types, and aim for 50 or more questions. With 13 answerable questions, one question is worth 7.7 points of recall, so small differences between models mean nothing.

## 6. Method

- **Recall@k** (k = 1, 3, 5): share of answerable questions with an expected chunk in the top k. For Q08, any of its three chunks counts.
- **MRR@10**: mean of 1 / rank of the first expected chunk; 0 if outside the top 10.
- **Doc@1**: share of questions whose top result is from the right document, even if the wrong chunk.
- **No-answer**: these questions are excluded from recall and MRR. The script compares top-1 similarity for answerable and no-answer questions and reports the threshold that best separates them.
- **Latency**: time to embed one query and search, 5 repeats per query after warm-up; p50 and p95.
- **Chunks/sec**: time to embed 2,000 chunks (the corpus repeated) at batch size 16.
- **RAM / VRAM**: peak process memory and peak CUDA memory allocated, one process per model.
- Settings: cosine similarity on normalised vectors, `max_seq_length` 512, chunk text prefixed with document title and section, fp16 on GPU (bf16 where fp16 is unsupported).

The synthetic chunks are short (about 40 words). Real chunks of 300-400 tokens will give lower chunks/sec and higher VRAM, so measure throughput on real data too.

## 7. Results

| Model                                              | R@1     | R@3   | R@5   | MRR@10 | Query p50 / p95 ms | Chunks/s | Peak RAM | Peak VRAM |
| -------------------------------------------------- | ------- | ----- | ----- | ------ | ------------------ | -------- | -------- | --------- |
| TF-IDF baseline (measured, lexical reference only) | 0.615   | 0.769 | 0.846 | 0.710  | n/a                | n/a      | n/a      | 0         |
| BGE-M3                                             | pending |       |       |        |                    |          |          |           |
| Qwen3-Embedding-0.6B                               | pending |       |       |        |                    |          |          |           |
| EmbeddingGemma-300M                                | pending |       |       |        |                    |          |          |           |
| Granite-Embedding-English-R2                       | pending |       |       |        |                    |          |          |           |
| Jina-Embeddings-v5-text-small                      | pending |       |       |        |                    |          |          |           |

The baseline shows the question set does its job: plain keyword matching gets every exact, short and technical question right at rank 1, and misses both paraphrased and both long questions at rank 1 (Q03 is not in its top 10 at all). A neural model has to win on those to be worth its cost. Its speed and memory are not comparable to a neural model's, so they are left out.

To fill the table, on the RTX 3060 machine:

```
pip install -U sentence-transformers psutil      # after installing torch with CUDA
huggingface-cli login                            # only needed for EmbeddingGemma
python make_dataset.py
python benchmark.py --models all
```

Output goes to `results/results.md`, which also breaks results down by query type and per question. The neural-model code path could not be executed during writing (only the baseline path was run), so expect to fix small issues on first run, most likely library versions for the Jina model. A model that fails to load is reported and skipped.

## 8. Recommendation and decision rules

**Primary: Qwen3-Embedding-0.6B. Backup: Granite-Embedding-English-R2.** Both are provisional.

Reasons the others are not picked on paper:

- **Jina v5 text-small** has the highest English mean score but a non-commercial licence. It is only an option if the system is strictly non-commercial, and that should be confirmed in writing first.
- **EmbeddingGemma-300M** is close to Qwen3 on mean score, but has a 2,048-token limit, a gated download under Google's Gemma terms, and no published retrieval-only score.
- **BGE-M3**: see section 4.

After running the benchmark on real HRD questions:

1. Rank by Recall@5, then MRR@10. Treat a gap of one or two questions as a tie.
2. Confirm Qwen3-0.6B as primary if it is best or tied for best.
3. Promote Granite English R2 if it is tied on quality, since it is smaller and faster, or if Qwen3's VRAM leaves too little room for the LLM.
4. If BGE-M3 or EmbeddingGemma wins by a clear margin (three or more questions out of 50), take the winner. The measurement on real data outranks this paper analysis.
5. If every model misses the same exact-term questions (form codes, policy ids), add keyword search alongside the embedding model before changing models.

## 9. Configuration

```yaml
embedding:
  primary:
    model: Qwen/Qwen3-Embedding-0.6B
    revision: <pin the commit hash you benchmarked>
    dtype: float16 # GPU; float32 on CPU
    dimensions: 1024 # full size; corpus is small, no need to truncate
    max_seq_length: 512
    batch_size: 16 # raise to 32 if peak VRAM allows
    normalize: true
    similarity: cosine
    padding_side: left
    query_prompt: "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:"
    document_prompt: none
  backup:
    model: ibm-granite/granite-embedding-english-r2
    dtype: float16
    dimensions: 768
    max_seq_length: 512
    query_prompt: none
    document_prompt: none
chunking:
  size_tokens: 300-400
  overlap_tokens: 50
  split_on: section headings first, then paragraphs
  prefix: "<document title> - <section heading>\n"
retrieval:
  top_k: 5
  no_answer_threshold: <set from the benchmark's no-answer table on real questions>
runtime:
  HF_HUB_OFFLINE: 1 # after the first download; nothing leaves the machine
```

- The two models produce different vector sizes (1024 vs 768). Switching to the backup means re-embedding the whole corpus into a separate index; keep both indexes built if fast failover matters.
- Changing the model, its revision, the query prompt or the chunk prefix also requires re-embedding.
- Qwen's card says a task-specific English instruction can help by a few points. Try `Given an HR policy question, retrieve the policy passages that answer it` against the default and keep whichever scores higher.

## 10. Files

- `embedding-benchmark.md`: this report.
- `benchmark.py`: the benchmark; one process per model, writes `results/results.md`.
- `make_dataset.py`: generates the synthetic `corpus.jsonl` and `queries.jsonl`. For real data, write those two files directly with the same fields (`chunk_id`, `doc_id`, `doc_title`, `section`, `text`; `query_id`, `type`, `query`, `expected_chunks`).

## Sources

- [BAAI/bge-m3 model card](https://huggingface.co/BAAI/bge-m3) and [memory requirements](https://huggingface.co/BAAI/bge-m3/discussions/64)
- [Qwen/Qwen3-Embedding-0.6B model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
- [google/embeddinggemma-300m model card](https://huggingface.co/google/embeddinggemma-300m)
- [ibm-granite/granite-embedding-english-r2 model card](https://huggingface.co/ibm-granite/granite-embedding-english-r2)
- [jinaai/jina-embeddings-v5-text-small model card](https://huggingface.co/jinaai/jina-embeddings-v5-text-small) and [retrieval variant](https://huggingface.co/jinaai/jina-embeddings-v5-text-small-retrieval)
- [A Comparative Study of Language Models for Khmer Retrieval-Augmented Question Answering (arXiv 2605.22099)](https://arxiv.org/abs/2605.22099)
