#!/usr/bin/env python3
"""Generate mentor-style questions from the real corpus, with ground truth.

Reads real/corpus.jsonl (written by excel_to_corpus.py) and writes
real/queries_mentor.jsonl. The questions imitate how busy staff really ask:
no sheet named, first names only, typos, lowercase, informal wording,
comparisons, calculations, and real-sounding students who do not exist.

Edit TEMPLATES below to add or change questions. Placeholders:
  {name} {first} {last} {typo}   a student and variants of their name
  {name2}                         a second student from the same sheet
  {sheet} {file}                  where the student's row is
  {column}                        a numeric column from that row

Run:   python3 make_mentor_questions.py
Then:  python3 benchmark.py --corpus real/corpus.jsonl --queries real/queries_mentor.jsonl \
           --out results_mentor --models tfidf-baseline bge-small-en arctic-l-v2 bge-m3
"""
import json
import random
import re
from pathlib import Path

HERE = Path(__file__).parent
CORPUS = HERE / "real" / "corpus.jsonl"
OUT = HERE / "real" / "queries_mentor.jsonl"
SEED = 11

# (type, template, answer rule)
# answer rules:  row      = the chosen student's row in the chosen sheet
#                student  = any row of that student in any sheet (sheet not named)
#                first    = any row of any student sharing that first name
#                card     = the chosen sheet's description chunk
#                pair     = rows of both students in the chosen sheet
#                none     = no answer (invented student)
TEMPLATES = [
    # no sheet named: the student may be in several sheets, any of their rows counts
    ("no-sheet", "what did {name} get in august", "student"),
    ("no-sheet", "{name} score?", "student"),
    ("no-sheet", "can you check {name}'s result", "student"),
    ("no-sheet", "how is {name} doing", "student"),
    ("no-sheet", "show me everything about {name}", "student"),
    ("no-sheet", "{name} attendance", "student"),
    ("no-sheet", "did {name} pass", "student"),
    ("no-sheet", "I need {name}'s marks for the report", "student"),
    # partial names
    ("partial-name", "what about {first}", "first"),
    ("partial-name", "{first} result in {sheet}", "first"),
    ("partial-name", "how many points did {first} get in {sheet}", "first"),
    ("partial-name", "check {last} in {sheet} please", "row"),
    # typos and informal wording
    ("typo", "{typo} {sheet} score", "row"),
    ("typo", "what is {typo}'s {column}", "student"),
    ("typo", "can u check {typo} in {sheet} pls", "row"),
    ("typo", "{typo} total in {sheet}??", "row"),
    ("informal", "bro what did {name} get in {sheet}", "row"),
    ("informal", "{name} {sheet} pls", "row"),
    ("informal", "hey can you find {name} for me, the {sheet} one", "row"),
    ("informal", "need {name} {column} from {sheet} asap", "row"),
    # exact, as a careful person would write it
    ("exact", "What is {name}'s {column} in the {sheet} sheet of {file}?", "row"),
    ("exact", "Please give me the {sheet} record of {name}.", "row"),
    ("exact", "In {file}, what did {name} score in {sheet}?", "row"),
    ("exact", "Find {name} in {sheet}.", "row"),
    # comparisons: both rows count
    ("comparison", "compare {name} and {name2} in {sheet}", "pair"),
    ("comparison", "who did better in {sheet}, {name} or {name2}?", "pair"),
    ("comparison", "{name} vs {name2} {sheet}", "pair"),
    # calculations: retrieval can only find the right sheet, so the sheet card is the answer
    ("calculation", "who got the highest total in {sheet}", "card"),
    ("calculation", "how many students are in {sheet}", "card"),
    ("calculation", "what is the average score in {sheet}", "card"),
    ("calculation", "who was absent the most in {sheet}", "card"),
    ("calculation", "list the students who failed in {sheet}", "card"),
    ("calculation", "top 5 students in {sheet}", "card"),
    # vague: no student, but a sheet or file is implied
    ("vague", "who is doing badly in {sheet}", "card"),
    ("vague", "any problems in {sheet} this month?", "card"),
    ("vague", "summary of {sheet}", "card"),
    ("vague", "what columns does {sheet} have", "card"),
    # invented students with realistic names
    ("no-answer", "what did {fake} get in {sheet}", "none"),
    ("no-answer", "{fake} score", "none"),
    ("no-answer", "is {fake} in {file}?", "none"),
    ("no-answer", "check {fake} attendance pls", "none"),
]

# Held-out set: different wording, written WITHOUT looking at the sheet-summary text,
# and a different random draw of students. Run with --heldout.
HELDOUT_TEMPLATES = [
    ("no-sheet", "pull up {name}", "student"),
    ("no-sheet", "update me on {name}", "student"),
    ("no-sheet", "does {name} have good marks", "student"),
    ("no-sheet", "{name}?", "student"),
    ("no-sheet", "where does {name} stand this month", "student"),
    ("no-sheet", "anything on {name}", "student"),
    ("partial-name", "{first} in {sheet}", "first"),
    ("partial-name", "{first}'s {sheet} numbers", "first"),
    ("partial-name", "is there a {first} in {sheet}?", "first"),
    ("reversed-name", "{last} {first} {sheet}", "row"),
    ("reversed-name", "find {last} {first} in {sheet}", "row"),
    ("typo", "{typo} in {sheet}", "row"),
    ("typo", "is {typo} ok in {sheet}", "row"),
    ("typo", "{typo} {sheet} marks pls", "row"),
    ("lowercase", "{lower} {sheet}", "row"),
    ("lowercase", "what did {lower} get in {sheet}", "row"),
    ("informal", "yo whats {name}'s {sheet} like", "row"),
    ("informal", "{name} in {sheet}, quick", "row"),
    ("informal", "gimme {name} from {sheet}", "row"),
    ("exact", "Retrieve the {sheet} row for {name} in {file}.", "row"),
    ("exact", "Show {name}'s {column} ({sheet}).", "row"),
    ("comparison", "{name} and {name2} {sheet} side by side", "pair"),
    ("comparison", "is {name} ahead of {name2} in {sheet}", "pair"),
    ("comparison", "{name} / {name2} - {sheet}", "pair"),
    ("calculation", "best student in {sheet}", "card"),
    ("calculation", "who did worst in {sheet}", "card"),
    ("calculation", "class ranking for {sheet}", "card"),
    ("calculation", "how big is the {sheet} group", "card"),
    ("calculation", "lowest marks in {sheet}", "card"),
    ("calculation", "which trainee leads {sheet}", "card"),
    ("vague", "overall picture of {sheet}", "card"),
    ("vague", "anyone struggling in {sheet}?", "card"),
    ("vague", "{sheet} class performance", "card"),
    ("vague", "tell me about the {sheet} sheet", "card"),
    ("no-answer", "pull up {fake}", "none"),
    ("no-answer", "{fake} {sheet}", "none"),
    ("no-answer", "is {fake} ok in {sheet}", "none"),
    ("no-answer", "does {fake} have good marks", "none"),
]

FAKE_NAMES = ["Sok Vannak", "Chea Sreymom", "Kong Piseth", "Nhim Dalin", "Ouk Sambath", "Prak Channary",
              "Sem Rotha", "Thy Kunthea", "Vong Sokchea", "Yun Bunthoeun", "Khut Sreyneang", "Long Veasna"]


def typo(name):
    """One realistic typo: swap two adjacent letters or drop one, inside a word of 4+ letters."""
    words = name.split()
    i = max(range(len(words)), key=lambda k: len(words[k]))
    w = words[i]
    if len(w) < 4:
        return name
    p = random.randrange(1, len(w) - 2)
    w = w[:p] + w[p + 1] + w[p] + w[p + 2:] if random.random() < 0.6 else w[:p] + w[p + 1:]
    words[i] = w
    return " ".join(words)


def main():
    import sys
    heldout = "--heldout" in sys.argv
    templates = HELDOUT_TEMPLATES if heldout else TEMPLATES
    out_path = HERE / "real" / ("queries_heldout.jsonl" if heldout else "queries_mentor.jsonl")
    prefix = "H" if heldout else "M"
    random.seed(SEED + 12 if heldout else SEED)
    chunks = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    rows = [c for c in chunks if not c["chunk_id"].endswith("#card")]
    cards = {c["doc_id"] + "#" + c["section"]: c["chunk_id"] for c in chunks if c["chunk_id"].endswith("#card")}

    # name column = second field of the row text ("No: 1; Name: ...")
    recs = []
    for c in rows:
        fields = [f.split(": ", 1) for f in c["text"].split("; ") if ": " in f]
        if len(fields) < 2:
            continue
        name = fields[1][1].strip()
        nums = [k for k, v in fields[2:] if re.fullmatch(r"-?\d+(\.\d+)?", v.strip())]
        recs.append(dict(name=name, key=name.lower(), first=name.split()[0], last=name.split()[-1],
                         sheet=c["section"], file=c["doc_id"], cid=c["chunk_id"], cols=nums[1:] or nums))
    by_name, by_first, by_sheet = {}, {}, {}
    for r in recs:
        by_name.setdefault(r["key"], []).append(r["cid"])
        by_first.setdefault(r["first"].lower(), []).append(r["cid"])
        by_sheet.setdefault((r["file"], r["sheet"]), []).append(r)
    real = set(by_name)
    fakes = [n for n in FAKE_NAMES if n.lower() not in real]

    out = []
    for qtype, tpl, rule in templates:
        pool = [r for r in recs if r["cols"]] if "{column}" in tpl else recs
        r = random.choice(pool)
        others = [o for o in by_sheet[(r["file"], r["sheet"])] if o["key"] != r["key"]]
        r2 = random.choice(others) if others else r
        q = tpl.format(name=r["name"], first=r["first"], last=r["last"], typo=typo(r["name"]),
                       lower=r["name"].lower(),
                       name2=r2["name"], sheet=r["sheet"], file=r["file"],
                       column=random.choice(r["cols"]) if r["cols"] else "score",
                       fake=random.choice(fakes))
        exp = {"row": [r["cid"]], "student": by_name[r["key"]], "first": by_first[r["first"].lower()],
               "card": [cards[r["file"] + "#" + r["sheet"]]], "pair": [r["cid"], r2["cid"]], "none": []}[rule]
        out.append(dict(query_id=f"{prefix}{len(out) + 1:03d}", type=qtype, query=q, expected_chunks=exp,
                        note=f"rule={rule}; {len(exp)} accepted chunk(s)"))

    with open(out_path, "w", encoding="utf-8") as f:
        for q in out:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    counts = {}
    for q in out:
        counts[q["type"]] = counts.get(q["type"], 0) + 1
    print(f"{len(out)} questions -> {out_path}")
    print(", ".join(f"{k} {v}" for k, v in counts.items()))
    print("Review them before running: the file contains student names, keep it local.")


if __name__ == "__main__":
    main()