# Embedding Model Benchmark for HRD Data: Final Report

**Author:** Panha
**Test dates:** 6, 19 and 21 October 2026
**Computer used:** NVIDIA RTX 3060 GPU, running under WSL
**Status:** Final. This report replaces the earlier interim reports.

## 1. Summary

I benchmarked local embedding models on the real HRD Excel files to choose a primary and a backup for retrieval. The first round (section 2) compared models on clean, generated questions and chose BGE-M3 as primary. The final round tested with questions written the way busy staff really ask, and found that the choice of model matters much less than the retrieval design around it.

**What changed**

| | First round | Final round |
|---|---|---|
| Questions | Clean and complete: "What is {name}'s {column} in the {sheet} sheet of {file}?" | Realistic: no sheet named, first name only, typos, lowercase, informal wording, comparisons, calculations, invented students |
| Best result, model alone | 85% first result | 54% to 60% first result |
| Best result, with the new design | not tested | **97% first result on an unseen question set** |

**Three design changes made the difference**

1. **Hybrid search:** keyword search and the embedding model together, scores added.
2. **Sheet filter:** when a question names a sheet, search only inside that sheet.
3. **Sheet summary chunks:** one extra chunk per sheet that describes what the sheet contains, written for questions like "who did best" or "how many students".

**Final recommendation** (decided by a rule agreed before the last run, section 7)

| Role | Model | Why |
|---|---|---|
| Primary | `BAAI/bge-m3` in hybrid mode, with the sheet filter | Equal best on both real question sets (33 of 34 unseen, 37 of 37). Handles inputs up to 8,192 tokens and 100+ languages, so it also covers documents and Khmer if they are added later. MIT licence. |
| Backup | `BAAI/bge-small-en-v1.5` in hybrid mode, with the sheet filter | Identical accuracy, question for question, at a tenth of the GPU memory (124 MB against 1,223 MB) and three times the speed (7 ms against 23 to 29 ms). Use it if the GPU is shared with an LLM. English only. |

Arctic Embed L v2.0 was one question behind on both sets and offers nothing BGE-M3 does not, so it was not selected.

This confirms the first round's choice of BGE-M3, now with the retrieval design that makes it work on realistic questions, and with a measured, cheap backup.

## 2. The first round: candidates and clean questions

**Goal and conditions.** Choose the best local embedding model for searching HRD data, plus a backup. The data is confidential, so everything runs on a local machine with no internet. The GPU has 6 to 8 GB of memory and may be shared with an LLM. Data and questions are in English.

**The data.** Three Excel workbooks with 14 sheets: student attendance for August 2026 (2 sheets), April monthly results (5) and August monthly results (7). 391 student rows. The files were read in place and never modified; each student row became one text chunk (`Column: value; ...`) and each sheet got one description chunk, 405 chunks in all. One file, `Attendance_List_Aug.xls.xls`, could not be opened because it is not a real Excel file.

**Candidates.** Five models were researched; the strongest on published results were measured on the real data. EmbeddingGemma-300M (gated download) and Jina v5 (non-commercial licence) could not be run.

| | BGE-M3 | Arctic Embed L v2.0 | bge-small-en-v1.5 | GTE-ModernBERT-base |
|---|---|---|---|---|
| Hugging Face id | `BAAI/bge-m3` | `Snowflake/snowflake-arctic-embed-l-v2.0` | `BAAI/bge-small-en-v1.5` | `Alibaba-NLP/gte-modernbert-base` |
| Parameters | about 568M | 568M | about 33M | 149M |
| Vector size | 1024 | 1024 | 384 | 768 |
| Longest input | 8,192 tokens | 8,192 tokens | 512 tokens | 8,192 tokens |
| Languages | 100+ | 74 | English only | English only |
| Licence | MIT | Apache 2.0 | MIT | Apache 2.0 |
| GPU memory (measured) | 1,185 MB | 1,185 MB | 109 MB | 396 MB |
| Query time (measured) | 15 ms | 16 ms | 9 ms | 15 ms |

**Clean questions.** 70 questions were generated from the data, 10 each of seven types (exact, paraphrased, short, long, technical, similar-document, no-answer), always naming the student, sheet and file. 60 had an answer.

| Model | First result | Top 3 | Top 5 | MRR |
|---|---|---|---|---|
| BGE-M3 | 51 of 60 (0.850) | **58 (0.967)** | **58 (0.967)** | **0.902** |
| Arctic Embed L v2.0 | **52 of 60 (0.867)** | 54 (0.900) | 57 (0.950) | 0.898 |
| bge-small-en-v1.5 | 49 of 60 (0.817) | 53 (0.883) | 57 (0.950) | 0.867 |
| Keyword search (TF-IDF) | 37 of 60 (0.617) | 52 (0.867) | 58 (0.967) | 0.744 |
| GTE-ModernBERT-base | 32 of 60 (0.533) | 45 (0.750) | 49 (0.817) | 0.644 |

**What the first round showed.** BGE-M3 and Arctic were tied and ahead of the rest; bge-small was close behind at a tenth of the memory; GTE-ModernBERT scored below keyword search and was dropped. Keyword search matched the best model in the top 5, because student names are exact words. No model could reject questions about invented students by similarity score without also rejecting 13% to 35% of real questions. BGE-M3 was chosen as primary and bge-small as backup.

## 3. Why a second round

The first round's questions were generated from a template and always named the student, the sheet and the file. Real staff do not ask like that. They write "what did Dara get in august", "check Rithy pls", or "who did worst in DevOps", often with a typo or only a first name. A system that scores well only on clean questions is not ready.

## 4. The realistic question set

A script generated 41 questions from the real data, using 40 wording patterns written to imitate busy colleagues. Each question has a known correct answer. The questions contain student names and stay on the local machine; only the patterns are shown here.

| Type | Count | Example pattern | What counts as correct |
|---|---|---|---|
| No sheet named | 8 | "what did {name} get in august", "how is {name} doing" | Any of that student's rows |
| Partial name | 4 | "what about {first}", "{first} result in {sheet}" | Any row of any student with that first name |
| Typo | 4 | "{name with one typo} {sheet} score" | That student's row in that sheet |
| Informal | 4 | "bro what did {name} get in {sheet}", "{name} {sheet} pls" | That student's row in that sheet |
| Exact | 4 | "What is {name}'s {column} in the {sheet} sheet of {file}?" | That student's row in that sheet |
| Comparison | 3 | "compare {name} and {name2} in {sheet}" | Either student's row in that sheet |
| Calculation | 6 | "who got the highest total in {sheet}", "how many students are in {sheet}" | The sheet's summary chunk. Retrieval can only find the right sheet; the calculation itself needs a table query. |
| Vague | 4 | "who is doing badly in {sheet}", "summary of {sheet}" | The sheet's summary chunk |
| No answer | 4 | "{invented name} score" | Nothing |

Most students appear in several sheets, so the hard part is finding the right student in the right sheet.

## 5. Results, step by step

37 answerable questions. "First result" means the correct chunk was the system's first guess.

### Step 0: models alone

| System | First result | Top 5 | MRR |
|---|---|---|---|
| Keyword search (TF-IDF) | 22 of 37 (0.595) | 30 (0.811) | 0.672 |
| Arctic Embed L v2.0 | 22 of 37 (0.595) | 27 (0.730) | 0.644 |
| bge-small-en-v1.5 | 20 of 37 (0.541) | 29 (0.784) | 0.642 |

All systems dropped a lot compared with the first round. Keyword search was as good as the embedding models, because a student's name is an exact word. The misses fell into two groups: the right student but the wrong sheet (9 questions, ranked 2 to 8), and the sheet summary not found at all (6 questions).

### Step 1: hybrid search

Each chunk gets two vectors, one from the embedding model and one from keyword search. A question's score is the sum of the two similarities.

| System | First result | Top 5 | MRR |
|---|---|---|---|
| Hybrid Arctic | 22 of 37 | 29 | 0.682 |
| Hybrid bge-small | 22 of 37 | 30 | 0.695 |

Hybrid was never worse than either part and improved the top 5, but did not change the first-result count. It fixes what the two methods disagree on; it cannot fix what both get wrong.

### Step 2: sheet filter

If a question contains a sheet name ("DevOps", "PP", "Official"), only chunks from that sheet are searched. 28 of the 41 questions named a sheet.

| System | First result | MRR |
|---|---|---|
| Keyword search + filter | 32 of 37 (0.865) | 0.865 |
| Hybrid Arctic + filter | 30 of 37 (0.811) | 0.815 |
| Hybrid bge-small + filter | 31 of 37 (0.838) | 0.838 |

All nine "wrong sheet" misses were fixed, including the typo, informal and comparison questions. The remaining misses were all sheet-summary questions.

### Step 3: sheet summary chunks

The description chunk for each sheet was rewritten to begin "Sheet summary: {sheet} sheet of {file}" and to say what the sheet is for: the number of students, their results, totals, averages, ranking, attendance and absences.

| System | First result | Top 3 | MRR |
|---|---|---|---|
| Keyword search + filter + summaries | 35 of 37 (0.946) | 37 | 0.973 |
| Hybrid Arctic + filter + summaries | 36 of 37 (0.973) | 37 | 0.986 |
| **Hybrid bge-small + filter + summaries** | **37 of 37 (1.000)** | 37 | 1.000 |

### The whole journey

| Stage | Hybrid bge-small, first result |
|---|---|
| Model alone | 20 of 37 (54%) |
| + keyword search | 22 of 37 (59%) |
| + sheet filter | 31 of 37 (84%) |
| + sheet summaries | 37 of 37 (100%) |

## 6. Held-out check

A perfect score on the questions used to shape the design proves little. So I generated a second set of 38 questions with different wording, a different random choice of students, and two new question types (name in reversed order, and all lowercase). The calculation and vague questions used words that do not appear in the summary text: "best", "worst", "ranking", "group", "leads", "struggling", "overall picture". The design was not changed after seeing these questions.

34 answerable questions:

| System | First result | Top 3 | MRR |
|---|---|---|---|
| **Hybrid bge-small + filter + summaries** | **33 of 34 (0.971)** | 33 | 0.971 |
| Hybrid Arctic + filter + summaries | 32 of 34 (0.941) | 33 | 0.956 |
| Keyword search + filter + summaries | 32 of 34 (0.941) | 33 | 0.956 |

Every question type scored 100% for hybrid bge-small except calculation (5 of 6). The one miss, "best student in {sheet}", was missed by all three systems: the summary text does not contain the words "best" or "student", so inside a large sheet the student rows outrank it. I left this as a known gap rather than tune the summary again.

## 7. Final run: all systems, both question sets

To settle the choice once, all four systems were run on both real question sets on 21 October, with the sheet filter and summary chunks. The rule was agreed before running: if a large model (BGE-M3 or Arctic) is within one question of bge-small on the unseen set, the large model becomes primary, because it also covers long documents and other languages; otherwise bge-small stays primary.

| System | Unseen set, first result (34) | Mentor-style set, first result (37) | Query time (median) | VRAM |
|---|---|---|---|---|
| **Hybrid BGE-M3** | **33** | **37** | 23 to 29 ms | 1,223 MB |
| Hybrid bge-small | **33** | **37** | 7 ms | 124 MB |
| Hybrid Arctic | 32 | 36 | 23 to 30 ms | 1,223 MB |
| Keyword search | 32 | 35 | 0.1 ms | 0 |

BGE-M3 and bge-small tied exactly: the same questions right and the same one question wrong (the "best student in {sheet}" miss). By the rule, BGE-M3 becomes primary and bge-small the backup.

Environment for these numbers: torch 2.6.0, transformers 4.51.3, sentence-transformers 4.1.0, CUDA 12.6. Earlier and later versions of these libraries failed to load one model or another, so the versions should be pinned.

## 8. Findings

**1. On realistic questions, the model alone is not good enough.** Every model fell to 54% to 60% first result. The misses were structural: the same student in several sheets, and summary chunks that could not compete with student rows.

**2. The retrieval design matters more than the model.** Three small changes moved the best system from 54% to 100% on the design questions and 97% on unseen questions. Switching between embedding models moved the score by a few points at most.

**3. Model size stopped mattering.** With the design in place, the 33M-parameter bge-small and the 568M-parameter BGE-M3 scored identically on both question sets, and Arctic was one question behind. The large model is chosen for what it covers later (documents, other languages), not for accuracy on this data.

**4. Keyword search is an essential part of the system, not a baseline to beat.** Student names are exact words. With the filter and summaries, keyword search alone reached 94% on the unseen questions. The embedding model adds the last few points, mainly on questions with unusual wording.

**5. The sheet filter needs name aliases in production.** It matches sheet names as written in the file, ignoring case. "siem reap" would not match a sheet called "Siemreap". A short alias list per sheet solves this.

**6. "No such student" is still a separate check.** As in the first round, similarity scores could not reject invented names without also rejecting real questions. The system should look the name up in the student list.

## 9. Recommended system design

1. **Index:** one chunk per student row, written as `Column: value; ...`, plus one summary chunk per sheet. Prefix every chunk with the workbook and sheet name.
2. **Search:** hybrid. Embed the question with `bge-m3` (or `bge-small-en-v1.5` as the backup) and with TF-IDF keyword vectors; add the two cosine similarities.
3. **Filter:** if the question contains a sheet name or an alias, restrict the search to that sheet.
4. **Not found:** check the name against the student list before searching.
5. **Calculations:** route "how many", "highest", "average", "ranking" questions to a query over the tables. Use retrieval only to pick the sheet.
6. **Return** the top 5 chunks to the LLM.

**Settings**

| Setting | Value |
|---|---|
| Embedding model | Primary `BAAI/bge-m3`, float16, 1024 dimensions, max 512 tokens (up to 8,192 for documents), batch 16. Backup `BAAI/bge-small-en-v1.5`, 384 dimensions, max 512 tokens. |
| Keyword vectors | TF-IDF over lowercase word tokens, cosine-normalised |
| Fusion | dense similarity + 1.0 × keyword similarity |
| Sheet filter | On, with an alias list per sheet |
| Top k | 5 |
| Measured cost | Primary: 23 to 29 ms per question, 1,223 MB VRAM, 2.1 GB RAM, about 270 chunks per second indexing. Backup: 7 ms, 124 MB VRAM, 1.4 GB RAM, about 1,300 chunks per second. |
| Library versions | torch 2.6.0, transformers 4.51.3, sentence-transformers 4.1.0 (pin these) |

## 10. Limitations

1. **The questions are still generated, not collected from staff.** They imitate real wording, and the held-out set was written without looking at the design, but questions from actual users would be a better test.
2. **Small numbers.** 37 and 34 questions; one question is about 3 percentage points.
3. **Sheet names must be spelled as in the file** for the filter to work. Aliases are not implemented yet.
4. **One calculation wording is missed** ("best student in ...").
5. **Library versions are fragile.** Three different version combinations failed to load at least one model before the pinned set worked.
6. **Calculations and "no such student" are designed, not built.** The benchmark measured retrieval only.
7. **One attendance file was not included** (section 2).

## 11. Next steps

- Collect 30 to 50 real questions from staff and re-run the same benchmark.
- Add sheet-name aliases to the filter.
- Build the table-query path for calculation questions and the name check for "not found".

## 12. Files

- `reports/embedding_benchmark_final.md`: this report.
- `real_data/excel_to_corpus.py`: reads the workbooks in place and builds the corpus, the summary chunks and the clean questions.
- `real_data/make_mentor_questions.py`: generates the realistic question set (`--heldout` for the second set).
- `benchmark.py`: now has hybrid model keys (`hybrid-bge-small`, `hybrid-arctic`, `hybrid-bge-m3`) and a `--sheet-filter` option.
- Results folders: `results_real` (first round), `results_heldout` (step-by-step runs) and `results_last_heldout` / `results_last_mentor` (the final run). These and the question files contain or derive from student records and stay on the local machine.

## References

- BGE-M3: https://huggingface.co/BAAI/bge-m3
- bge-small-en-v1.5: https://huggingface.co/BAAI/bge-small-en-v1.5
- Snowflake Arctic Embed L v2.0: https://huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0
- GTE-ModernBERT-base: https://huggingface.co/Alibaba-NLP/gte-modernbert-base