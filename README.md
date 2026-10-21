# Embedding Model Benchmark

Selecting a local embedding model for HRD data, measured on an RTX 3060.

**Result (21 Oct 2026, final benchmark): `BAAI/bge-m3` as primary, `BAAI/bge-small-en-v1.5` as backup, both in hybrid mode (embedding plus keyword search) with a sheet filter.** The two scored identically, 97% first-result on unseen realistic questions; the retrieval design mattered more than the model. See `reports/embedding_benchmark_final.md`.

## Two benchmarks

| | Synthetic | Real data |
|---|---|---|
| Folder | `synthetic/` | `real_data/` |
| Report | `reports/embedding_benchmark.md` | `reports/embedding_benchmark_real_data.md`, then `reports/embedding_benchmark_final.md` |
| Data | 42 invented HR policy chunks, 16 questions | HRD Excel workbooks: 405 chunks, 70 generated questions |
| Purpose | Candidate research, specifications, first measurements | Confirming the choice on the actual data |
| Picks | Arctic Embed L v2.0, GTE-ModernBERT-base | **BGE-M3, bge-small-en-v1.5** |

The synthetic test turned out to be too easy to separate the models, and its backup pick failed on real data. Use the real-data report for decisions.

## Layout

```
benchmark.py                 shared benchmark script
synthetic/
    embedding_benchmark.md
    make_dataset.py          writes corpus.jsonl and queries.jsonl
    corpus.jsonl
    queries.jsonl
    results/
real_data/
    embedding_benchmark_real_data.md
    excel_to_corpus.py       builds the corpus and questions from the workbooks
    inspect_layout.py        shows sheet layout with every cell masked
    docs/                    HRD workbooks (not in git)
    real/                    generated corpus and questions (not in git)
    results_real/            benchmark output (not in git)
```

## Setup

```
pip install -U sentence-transformers psutil openpyxl xlrd     # after installing torch with CUDA
```

## Running

From the project root.

Synthetic:

```
python3 synthetic/make_dataset.py
python3 benchmark.py --corpus synthetic/corpus.jsonl --queries synthetic/queries.jsonl --out synthetic/results --models tfidf-baseline bge-m3 arctic-l-v2 gte-modernbert bge-small-en
```

Real data (place the workbooks in `real_data/docs/` first):

```
python3 real_data/excel_to_corpus.py real_data/docs --out real_data/real
python3 benchmark.py --corpus real_data/real/corpus.jsonl --queries real_data/real/queries.jsonl --out real_data/results_real --models tfidf-baseline bge-small-en arctic-l-v2 bge-m3
```

Models are downloaded from Hugging Face on first use and cached. Everything else runs locally.

## Final benchmark: realistic questions and retrieval design

```
cd real_data
python3 make_mentor_questions.py              # 41 mentor-style questions -> real/queries_mentor.jsonl
python3 make_mentor_questions.py --heldout    # 38 unseen-wording questions -> real/queries_heldout.jsonl
python3 ../benchmark.py --corpus real/corpus.jsonl --queries real/queries_heldout.jsonl --out results_heldout --sheet-filter --models tfidf-baseline hybrid-arctic hybrid-bge-small
```

Pinned environment for the final run: torch 2.6.0, transformers 4.51.3, sentence-transformers 4.1.0.

`benchmark.py` gained hybrid model keys (`hybrid-bge-small`, `hybrid-arctic`, `hybrid-bge-m3`) and a `--sheet-filter` option; `excel_to_corpus.py` now writes a summary chunk per sheet.

## Confidential data

`real_data/docs/`, `real_data/real/` and every `real_data/results_*/` folder contain or derive from student records and are excluded by `.gitignore`. Do not commit them. The real-data report contains aggregate results only.