#!/usr/bin/env python3
"""Local embedding-model retrieval benchmark.

Measures, per model: Recall@1/3/5, MRR@10, document-level hit@1, no-answer
separation, query latency (p50/p95), indexing throughput (chunks/sec),
peak RAM and peak VRAM. Each model runs in its own process so memory
numbers are not polluted by the previous model.

Setup (on the machine that will serve the model):
    pip install -U sentence-transformers psutil      # torch with CUDA first
    huggingface-cli login                            # only for embeddinggemma (gated)

Run:
    python make_dataset.py                           # writes corpus.jsonl / queries.jsonl
    python benchmark.py --models all                 # all five candidates + TF-IDF baseline
    python benchmark.py --models qwen3-0.6b bge-m3 --batch-size 16

Everything runs locally; after the first download set HF_HUB_OFFLINE=1 and
no network access is needed. Output: results/results.md and results/*.json
"""
import argparse
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent

# hf: Hugging Face id. dtype: GPU precision (CPU always runs float32).
# *_prompt_name: prompt stored in the model's sentence-transformers config.
MODELS = {
    "bge-m3": dict(hf="BAAI/bge-m3", dtype="float16"),
    "qwen3-0.6b": dict(hf="Qwen/Qwen3-Embedding-0.6B", dtype="float16",
                       query_prompt_name="query",
                       tokenizer_kwargs={"padding_side": "left"}),
    # EmbeddingGemma does not support float16 (model card) -> bfloat16.
    "embeddinggemma": dict(hf="google/embeddinggemma-300m", dtype="bfloat16",
                           query_prompt_name="query", doc_prompt_name="document"),
    "granite-en-r2": dict(hf="ibm-granite/granite-embedding-english-r2", dtype="float16"),
    # CC BY-NC 4.0: non-commercial use only. Needs transformers>=5.1, peft.
    "jina-v5-small": dict(hf="jinaai/jina-embeddings-v5-text-small-retrieval", dtype="bfloat16",
                          query_prompt_name="query", doc_prompt_name="document",
                          trust_remote_code=True),
    # Replacements for the two candidates that could not be run. Both Apache 2.0, not gated.
    "arctic-l-v2": dict(hf="Snowflake/snowflake-arctic-embed-l-v2.0", dtype="float16",
                        query_prompt_name="query"),
    "gte-modernbert": dict(hf="Alibaba-NLP/gte-modernbert-base", dtype="float16"),
    # Lexical reference point, no model download. Not a candidate.
    "tfidf-baseline": dict(backend="tfidf"),
}


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def chunk_text(c, with_heading):
    return f"{c['doc_title']} - {c['section']}\n{c['text']}" if with_heading else c["text"]


def peak_ram_mb():
    try:
        import psutil
        mi = psutil.Process().memory_info()
        peak = getattr(mi, "peak_wset", None)          # Windows
        if peak:
            return peak / 2**20
    except ImportError:
        pass
    try:
        import resource
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # bytes on macOS, KB on Linux
        return r / 2**20 if sys.platform == "darwin" else r / 1024
    except ImportError:
        return float("nan")


# ----------------------------------------------------------------- backends
class TfidfBackend:
    """Plain TF-IDF cosine. A lexical floor to compare the neural models against."""
    name = "tfidf"
    device = "cpu"
    dim = None

    def __init__(self, corpus_texts):
        self.tok = lambda s: re.findall(r"[a-z0-9_:]+", s.lower())
        vocab = {}
        for t in corpus_texts:
            for w in set(self.tok(t)):
                vocab[w] = vocab.get(w, 0) + 1
        self.index = {w: i for i, w in enumerate(sorted(vocab))}
        n = len(corpus_texts)
        self.idf = np.zeros(len(self.index), dtype=np.float32)
        for w, i in self.index.items():
            self.idf[i] = math.log((1 + n) / (1 + vocab[w])) + 1
        self.dim = len(self.index)

    def _enc(self, texts):
        m = np.zeros((len(texts), self.dim), dtype=np.float32)
        for r, t in enumerate(texts):
            for w in self.tok(t):
                i = self.index.get(w)
                if i is not None:
                    m[r, i] += 1
        m *= self.idf
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        return m / np.maximum(norms, 1e-9)

    def encode_docs(self, texts, batch_size):
        return self._enc(texts)

    def encode_query(self, text):
        return self._enc([text])[0]

    def count_tokens(self, texts):
        return [len(self.tok(t)) for t in texts]

    def vram_mb(self):
        return 0.0


class STBackend:
    def __init__(self, cfg, device, max_seq_length):
        import torch
        from sentence_transformers import SentenceTransformer
        self.torch = torch
        self.cfg = cfg
        self.device = device or (
            "cuda" if torch.cuda.is_available() else "cpu")
        kwargs = {}
        if cfg.get("tokenizer_kwargs"):
            kwargs["tokenizer_kwargs"] = cfg["tokenizer_kwargs"]
        if cfg.get("trust_remote_code"):
            kwargs["trust_remote_code"] = True
        self.model = SentenceTransformer(
            cfg["hf"], device=self.device, **kwargs)
        self.dtype = "float32"
        if self.device == "cuda":
            self.dtype = cfg.get("dtype", "float32")
            if self.dtype == "float16":
                self.model.half()
            elif self.dtype == "bfloat16":
                self.model.to(torch.bfloat16)
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()        # ignore the float32 load transient
        self.model.max_seq_length = max_seq_length
        self.dim = self.model.get_sentence_embedding_dimension()

    def _encode(self, texts, batch_size, prompt_name):
        kw = dict(batch_size=batch_size, normalize_embeddings=True,
                  convert_to_numpy=True, show_progress_bar=False)
        if prompt_name:
            kw["prompt_name"] = prompt_name
        out = self.model.encode(texts, **kw)
        if self.device == "cuda":
            self.torch.cuda.synchronize()
        return np.asarray(out, dtype=np.float32)

    def encode_docs(self, texts, batch_size):
        return self._encode(texts, batch_size, self.cfg.get("doc_prompt_name"))

    def encode_query(self, text):
        return self._encode([text], 1, self.cfg.get("query_prompt_name"))[0]

    def count_tokens(self, texts):
        tok = self.model.tokenizer
        return [len(tok(t, truncation=True, max_length=self.model.max_seq_length)["input_ids"])
                for t in texts]

    def vram_mb(self):
        if self.device != "cuda":
            return 0.0
        return self.torch.cuda.max_memory_allocated() / 2**20


# ------------------------------------------------------------------ metrics
def evaluate(queries, chunks, doc_emb, backend, latency_repeats):
    ids = [c["chunk_id"] for c in chunks]
    doc_of = {c["chunk_id"]: c["doc_id"] for c in chunks}
    for q in queries[:3]:                               # warm-up
        backend.encode_query(q["query"])
    rows, lat = [], []
    for q in queries:
        times = []
        for _ in range(latency_repeats):
            t0 = time.perf_counter()
            qv = backend.encode_query(q["query"])
            scores = doc_emb @ qv
            order = np.argsort(-scores)[:10]
            times.append((time.perf_counter() - t0) * 1000)
        lat.extend(times)
        ranked = [ids[i] for i in order]
        exp = q["expected_chunks"]
        rank = next((r for r, cid in enumerate(ranked, 1) if cid in exp), None)
        rows.append(dict(query_id=q["query_id"], type=q["type"], expected=exp,
                         top1=ranked[0], top1_score=float(scores[order[0]]),
                         top3=ranked[:3], rank=rank,
                         doc_hit1=bool(exp) and doc_of[ranked[0]] in {
            doc_of[e] for e in exp},
            latency_ms=statistics.median(times)))
    ans = [r for r in rows if r["expected"]]
    noans = [r for r in rows if not r["expected"]]

    def agg(rs):
        n = len(rs)
        return dict(n=n,
                    recall_at_1=sum(
                        r["rank"] is not None and r["rank"] <= 1 for r in rs) / n,
                    recall_at_3=sum(
                        r["rank"] is not None and r["rank"] <= 3 for r in rs) / n,
                    recall_at_5=sum(
                        r["rank"] is not None and r["rank"] <= 5 for r in rs) / n,
                    mrr_at_10=sum(1 / r["rank"] for r in rs if r["rank"]) / n,
                    doc_hit_at_1=sum(r["doc_hit1"] for r in rs) / n)

    overall = agg(ans)
    by_type = {t: agg([r for r in ans if r["type"] == t])
               for t in sorted({r["type"] for r in ans})}

    # No-answer handling: can a top-1 score threshold separate answerable from unanswerable?
    na = None
    if noans:
        a = sorted(r["top1_score"] for r in ans)
        n_ = sorted(r["top1_score"] for r in noans)
        allv = sorted(a + n_)
        best = (-1.0, None)
        for lo, hi in zip(allv, allv[1:]):
            t = (lo + hi) / 2
            bal = (sum(x >= t for x in a) / len(a) +
                   sum(x < t for x in n_) / len(n_)) / 2
            if bal > best[0]:
                best = (bal, t)
        t = best[1]
        na = dict(n=len(noans), mean_top1_answerable=statistics.mean(a),
                  mean_top1_no_answer=statistics.mean(n_), max_top1_no_answer=max(n_),
                  min_top1_answerable=min(a), threshold=t,
                  rejected_no_answer=sum(x < t for x in n_) / len(n_),
                  kept_answerable=sum(x >= t for x in a) / len(a))
    lat.sort()
    latency = dict(p50_ms=statistics.median(
        lat), p95_ms=lat[min(len(lat) - 1, int(0.95 * len(lat)))])
    return dict(overall=overall, by_type=by_type, no_answer=na, latency=latency, per_query=rows)


def worker(args):
    key = args.worker
    cfg = MODELS[key]
    chunks = read_jsonl(args.corpus)
    queries = read_jsonl(args.queries)
    texts = [chunk_text(c, not args.no_heading) for c in chunks]

    t0 = time.perf_counter()
    if cfg.get("backend") == "tfidf":
        backend = TfidfBackend(texts)
    else:
        backend = STBackend(cfg, args.device, args.max_seq_length)
    load_s = time.perf_counter() - t0

    doc_emb = backend.encode_docs(texts, args.batch_size)

    # Indexing throughput on a replicated corpus (the real one is too small to time).
    n = max(args.throughput_chunks, len(texts))
    big = (texts * math.ceil(n / len(texts)))[:n]
    backend.encode_docs(big[:args.batch_size],
                        args.batch_size)             # warm-up
    t0 = time.perf_counter()
    backend.encode_docs(big, args.batch_size)
    dt = time.perf_counter() - t0
    tokens = backend.count_tokens(texts)
    mean_tok = sum(tokens) / len(tokens)

    res = evaluate(queries, chunks, doc_emb, backend, args.latency_repeats)
    res.update(model=key, hf=cfg.get("hf", "-"), device=backend.device,
               dtype=getattr(backend, "dtype", "float32"), dim=int(doc_emb.shape[1]),
               batch_size=args.batch_size, max_seq_length=args.max_seq_length,
               load_seconds=load_s, chunks_per_sec=n / dt, mean_tokens_per_chunk=mean_tok,
               tokens_per_sec=n * mean_tok / dt, peak_ram_mb=peak_ram_mb(),
               peak_vram_mb=backend.vram_mb(), n_chunks=len(chunks))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{key}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")


# ------------------------------------------------------------------- report
def fmt(x, nd=3):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def report(results, failures, out):
    L = ["# Embedding benchmark results", ""]
    if results:
        r0 = results[0]
        L += [f"Corpus: {r0['n_chunks']} chunks. Answerable queries: {r0['overall']['n']}. "
              f"No-answer queries: {r0['no_answer']['n'] if r0['no_answer'] else 0}. "
              f"max_seq_length={r0['max_seq_length']}, batch_size={r0['batch_size']}.", ""]
    L += ["## Summary", "",
          "| Model | Device / dtype | Dim | R@1 | R@3 | R@5 | MRR@10 | Doc@1 | Query p50 ms | Query p95 ms | Chunks/s | Peak RAM MB | Peak VRAM MB |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        o, la = r["overall"], r["latency"]
        L.append(f"| {r['model']} | {r['device']} / {r['dtype']} | {r['dim']} | {fmt(o['recall_at_1'])} | "
                 f"{fmt(o['recall_at_3'])} | {fmt(o['recall_at_5'])} | {fmt(o['mrr_at_10'])} | "
                 f"{fmt(o['doc_hit_at_1'])} | {fmt(la['p50_ms'], 1)} | {fmt(la['p95_ms'], 1)} | "
                 f"{fmt(r['chunks_per_sec'], 1)} | {fmt(r['peak_ram_mb'], 0)} | {fmt(r['peak_vram_mb'], 0)} |")
    L += ["", "Chunks/s is measured on chunks averaging the token counts below; longer chunks are slower.", "",
          "| Model | Mean tokens/chunk | Tokens/s | Load s |", "|---|---|---|---|"]
    for r in results:
        L.append(
            f"| {r['model']} | {fmt(r['mean_tokens_per_chunk'], 0)} | {fmt(r['tokens_per_sec'], 0)} | {fmt(r['load_seconds'], 1)} |")

    types = sorted({t for r in results for t in r["by_type"]})
    L += ["", "## Recall@1 / MRR@10 by query type", "", "| Model | " + " | ".join(types) + " |",
          "|---|" + "---|" * len(types)]
    for r in results:
        cells = [f"{fmt(r['by_type'][t]['recall_at_1'], 2)} / {fmt(r['by_type'][t]['mrr_at_10'], 2)}"
                 if t in r["by_type"] else "-" for t in types]
        L.append(f"| {r['model']} | " + " | ".join(cells) + " |")

    L += ["", "## No-answer queries", "",
          "A usable model keeps answerable queries above the threshold and no-answer queries below it. "
          "The threshold is fitted on this same small set, so treat it as a starting point.", "",
          "| Model | Mean top-1 (answerable) | Min top-1 (answerable) | Max top-1 (no-answer) | Threshold | No-answer rejected | Answerable kept |",
          "|---|---|---|---|---|---|---|"]
    for r in results:
        na = r["no_answer"]
        if na:
            L.append(f"| {r['model']} | {fmt(na['mean_top1_answerable'])} | {fmt(na['min_top1_answerable'])} | "
                     f"{fmt(na['max_top1_no_answer'])} | {fmt(na['threshold'])} | "
                     f"{fmt(na['rejected_no_answer'], 2)} | {fmt(na['kept_answerable'], 2)} |")

    L += ["",
          "## Per-query rank of the first expected chunk (blank = not in top 10)", ""]
    if results:
        qids = [q["query_id"]
                for q in results[0]["per_query"] if q["expected"]]
        L += ["| Model | " + " | ".join(qids) +
              " |", "|---|" + "---|" * len(qids)]
        for r in results:
            ranks = {q["query_id"]: q["rank"] for q in r["per_query"]}
            L.append(f"| {r['model']} | " + " | ".join(str(ranks[q])
                     if ranks[q] else " " for q in qids) + " |")
    if failures:
        L += ["", "## Models that did not run", ""]
        L += [f"- {k}: {msg}" for k, msg in failures]
    (out / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\n".join(L))


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--models", nargs="+",
                   default=["all"], help=f"all or any of: {', '.join(MODELS)}")
    p.add_argument("--corpus", default=str(HERE / "corpus.jsonl"))
    p.add_argument("--queries", default=str(HERE / "queries.jsonl"))
    p.add_argument("--out", default=str(HERE / "results"))
    p.add_argument("--device", default=None,
                   help="cuda or cpu (default: cuda if available)")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--max-seq-length", type=int, default=512)
    p.add_argument("--throughput-chunks", type=int, default=2000)
    p.add_argument("--latency-repeats", type=int, default=5)
    p.add_argument("--no-heading", action="store_true",
                   help="embed chunk text without 'title - section' prefix")
    p.add_argument("--worker", default=None, help=argparse.SUPPRESS)
    args = p.parse_args()

    if args.worker:
        return worker(args)

    keys = list(MODELS) if args.models == ["all"] else args.models
    unknown = [k for k in keys if k not in MODELS]
    if unknown:
        sys.exit(f"unknown model(s): {unknown}; choose from {list(MODELS)}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results, failures = [], []
    passthrough = [a for a in sys.argv[1:]]
    if "--models" in passthrough:                      # strip --models and its values
        i = passthrough.index("--models")
        j = i + 1
        while j < len(passthrough) and not passthrough[j].startswith("--"):
            j += 1
        del passthrough[i:j]
    for k in keys:
        print(f"=== {k} ===", flush=True)
        f = out / f"{k}.json"
        if f.exists():
            f.unlink()
        proc = subprocess.run([sys.executable, os.path.abspath(__file__), "--worker", k] + passthrough,
                              capture_output=True, text=True)
        if proc.returncode == 0 and f.exists():
            results.append(json.loads(f.read_text(encoding="utf-8")))
        else:
            tail = (proc.stderr or "").strip(
            ).splitlines()[-1:] or ["no error output"]
            failures.append((k, tail[0][:300]))
            print(f"FAILED: {tail[0][:300]}", flush=True)
    report(results, failures, out)


if __name__ == "__main__":
    main()
