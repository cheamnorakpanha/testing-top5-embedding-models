# Embedding Benchmark, Part 2: Realistic Questions and Retrieval Design

**Author:** Panha
**Test date:** 19 October 2026
**Computer used:** NVIDIA RTX 3060 GPU, running under WSL
**Follows:** Embedding Model Benchmark on Real HRD Data (Part 1, 6 October 2026)

## 1. Summary

Part 1 compared embedding models on clean, generated questions and chose BGE-M3 as primary. In Part 2 I tested with questions written the way busy staff really ask, and found that the choice of model matters much less than the retrieval design around it.

**What changed**

| | Part 1 | Part 2 |
|---|---|---|
| Questions | Clean and complete: "What is {name}'s {column} in the {sheet} sheet of {file}?" | Realistic: no sheet named, first name only, typos, lowercase, informal wording, comparisons, calculations, invented students |
| Best result, model alone | 85% first result | 54% to 60% first result |
| Best result, with the new design | not tested | **97% first result on an unseen question set** |

**Three design changes made the difference**

1. **Hybrid search:** keyword search and the embedding model together, scores added.
2. **Sheet filter:** when a question names a sheet, search only inside that sheet.
3. **Sheet summary chunks:** one extra chunk per sheet that describes what the sheet contains, written for questions like "who did best" or "how many students".

**Revised recommendation**

| Role | Model | Why |
|---|---|---|
| Primary | `BAAI/bge-small-en-v1.5` in hybrid mode, with the sheet filter | Best score on the unseen questions (33 of 34 first result). 7 ms per question, 121 MB of GPU memory. |
| Backup | `Snowflake/snowflake-arctic-embed-l-v2.0` in hybrid mode, with the sheet filter | 32 of 34. Same design, larger model, for use if a bigger model is wanted later (for example for Khmer text). |

BGE-M3, the Part 1 primary, was not re-run in Part 2 because of a library version problem on the test machine. Given the results, it is unlikely to change the conclusion: on this data the retrieval design decides the outcome, not the model size.

## 2. Why a second round

Part 1's questions were generated from a template and always named the student, the sheet and the file. Real staff do not ask like that. They write "what did Dara get in august", "check Rithy pls", or "who did worst in DevOps", often with a typo or only a first name. A system that scores well only on clean questions is not ready.

## 3. The realistic question set

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

## 4. Results, step by step

37 answerable questions. "First result" means the correct chunk was the system's first guess.

### Step 0: models alone

| System | First result | Top 5 | MRR |
|---|---|---|---|
| Keyword search (TF-IDF) | 22 of 37 (0.595) | 30 (0.811) | 0.672 |
| Arctic Embed L v2.0 | 22 of 37 (0.595) | 27 (0.730) | 0.644 |
| bge-small-en-v1.5 | 20 of 37 (0.541) | 29 (0.784) | 0.642 |

All systems dropped a lot compared with Part 1. Keyword search was as good as the embedding models, because a student's name is an exact word. The misses fell into two groups: the right student but the wrong sheet (9 questions, ranked 2 to 8), and the sheet summary not found at all (6 questions).

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

## 5. Held-out check

A perfect score on the questions used to shape the design proves little. So I generated a second set of 38 questions with different wording, a different random choice of students, and two new question types (name in reversed order, and all lowercase). The calculation and vague questions used words that do not appear in the summary text: "best", "worst", "ranking", "group", "leads", "struggling", "overall picture". The design was not changed after seeing these questions.

34 answerable questions:

| System | First result | Top 3 | MRR |
|---|---|---|---|
| **Hybrid bge-small + filter + summaries** | **33 of 34 (0.971)** | 33 | 0.971 |
| Hybrid Arctic + filter + summaries | 32 of 34 (0.941) | 33 | 0.956 |
| Keyword search + filter + summaries | 32 of 34 (0.941) | 33 | 0.956 |

Every question type scored 100% for hybrid bge-small except calculation (5 of 6). The one miss, "best student in {sheet}", was missed by all three systems: the summary text does not contain the words "best" or "student", so inside a large sheet the student rows outrank it. I left this as a known gap rather than tune the summary again.

## 6. Findings

**1. On realistic questions, the model alone is not good enough.** Every model fell to 54% to 60% first result. The misses were structural: the same student in several sheets, and summary chunks that could not compete with student rows.

**2. The retrieval design matters more than the model.** Three small changes moved the best system from 54% to 100% on the design questions and 97% on unseen questions. Switching between embedding models moved the score by a few points at most.

**3. The smallest model is now the best choice.** With the design in place, hybrid bge-small matched or beat hybrid Arctic on both question sets, at a tenth of the GPU memory and three times the speed.

**4. Keyword search is an essential part of the system, not a baseline to beat.** Student names are exact words. With the filter and summaries, keyword search alone reached 94% on the unseen questions. The embedding model adds the last few points, mainly on questions with unusual wording.

**5. The sheet filter needs name aliases in production.** It matches sheet names as written in the file, ignoring case. "siem reap" would not match a sheet called "Siemreap". A short alias list per sheet solves this.

**6. "No such student" is still a separate check.** As in Part 1, similarity scores could not reject invented names without also rejecting real questions. The system should look the name up in the student list.

## 7. Recommended system design

1. **Index:** one chunk per student row, written as `Column: value; ...`, plus one summary chunk per sheet. Prefix every chunk with the workbook and sheet name.
2. **Search:** hybrid. Embed the question with `bge-small-en-v1.5` and with TF-IDF keyword vectors; add the two cosine similarities.
3. **Filter:** if the question contains a sheet name or an alias, restrict the search to that sheet.
4. **Not found:** check the name against the student list before searching.
5. **Calculations:** route "how many", "highest", "average", "ranking" questions to a query over the tables. Use retrieval only to pick the sheet.
6. **Return** the top 5 chunks to the LLM.

**Settings**

| Setting | Value |
|---|---|
| Embedding model | `BAAI/bge-small-en-v1.5`, float16, 384 dimensions, max 512 tokens, batch 16 |
| Keyword vectors | TF-IDF over lowercase word tokens, cosine-normalised |
| Fusion | dense similarity + 1.0 × keyword similarity |
| Sheet filter | On, with an alias list per sheet |
| Top k | 5 |
| Measured cost | 7 ms per question, 121 MB VRAM, 1.3 GB RAM, about 1,100 chunks per second indexing |

## 8. Limitations

1. **The questions are still generated, not collected from staff.** They imitate real wording, and the held-out set was written without looking at the design, but questions from actual users would be a better test.
2. **Small numbers.** 37 and 34 questions; one question is about 3 percentage points.
3. **Sheet names must be spelled as in the file** for the filter to work. Aliases are not implemented yet.
4. **One calculation wording is missed** ("best student in ...").
5. **BGE-M3 was not re-run** in Part 2.
6. **Calculations and "no such student" are designed, not built.** The benchmark measured retrieval only.
7. **One attendance file was not included**, as in Part 1.

## 9. Next steps

- Collect 30 to 50 real questions from staff and re-run the same benchmark.
- Add sheet-name aliases to the filter.
- Build the table-query path for calculation questions and the name check for "not found".
- Optionally re-run BGE-M3 in hybrid mode after upgrading torch, for completeness.

## 10. Files

- `real_data/make_mentor_questions.py`: generates the realistic question set (`--heldout` for the second set).
- `real_data/excel_to_corpus.py`: builds the corpus with the new summary chunks.
- `benchmark.py`: now has hybrid model keys (`hybrid-bge-small`, `hybrid-arctic`, `hybrid-bge-m3`) and a `--sheet-filter` option.
- Results folders: `results_mentor`, `results_hybrid`, `results_filter`, `results_final`, `results_heldout`. These and the question files contain or derive from student records and stay on the local machine.