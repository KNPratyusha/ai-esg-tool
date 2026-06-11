"""Faithfulness / groundedness eval for Raga (the BRSR RAG assistant in raga.py).

Measures whether Raga's answers are actually grounded in the retrieved BRSR
excerpts — the property that matters most in a regulated domain — and whether it
correctly *refuses* questions whose answers aren't in the document.

Built for flaky free tiers: calls are paced (--sleep) to stay under rate limits,
each call is retried with exponential backoff on 429/5xx, and any case that still
fails is recorded and skipped so one hiccup never sinks the whole run.

Run from the repo root:

    export GEMINI_API_KEY="..."              # free key at https://aistudio.google.com
    python -m evals.faithfulness_eval        # full suite (paced for free tier)
    python -m evals.faithfulness_eval --max 4   # quick smoke test
"""
import os
import re
import sys
import json
import time
import argparse
from pathlib import Path

from google.genai import errors as genai_errors

# Make the repo root importable so we can reuse the real RAG pipeline (raga.py).
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

REFUSAL_MARKER = "couldn't find specific information"
CITATION_RE = re.compile(r"(?i)\b(page|p\.|pg|principle|section)\b")
DATASET = Path(__file__).parent / "dataset.jsonl"
FAITH_SCORE = {"SUPPORTED": 1.0, "PARTIAL": 0.5, "UNSUPPORTED": 0.0}
TRANSIENT_CODES = {429, 500, 502, 503, 504}


def load_cases(max_cases=None):
    cases = []
    with open(DATASET, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases[:max_cases] if max_cases else cases


def with_retry(fn, *args, attempts=6, base=2.0, **kwargs):
    """Call fn, retrying transient API errors (rate limits / 5xx) with backoff."""
    for i in range(attempts):
        try:
            return fn(*args, **kwargs)
        except genai_errors.APIError as e:
            code = getattr(e, "code", None) or getattr(e, "status_code", None)
            transient = code in TRANSIENT_CODES or "UNAVAILABLE" in str(e).upper()
            if not transient or i == attempts - 1:
                raise
            wait = base * (2 ** i)
            print(f"   ⚠ transient API error ({code or 'unknown'}) — retry {i + 1}/{attempts} in {wait:.0f}s")
            time.sleep(wait)


def refused(answer: str) -> bool:
    return REFUSAL_MARKER in answer.lower()


def has_citation(answer: str) -> bool:
    return bool(CITATION_RE.search(answer))


def coverage(answer: str, must_mention):
    """Lexical coverage of expected topics — a cheap secondary signal."""
    if not must_mention:
        return None
    hits = sum(1 for kw in must_mention if kw.lower() in answer.lower())
    return round(hits / len(must_mention), 2)


def pct(n, d):
    return f"{n}/{d} ({(100 * n / d):.0f}%)" if d else "n/a"


def main():
    ap = argparse.ArgumentParser(description="Faithfulness eval for Raga (BRSR RAG).")
    ap.add_argument("--max", type=int, default=None, help="limit number of cases")
    ap.add_argument("--pdf", default=os.environ.get("BRSR_PDF", "brsr.pdf"))
    ap.add_argument("--sleep", type=float, default=4.0,
                    help="seconds to pause between cases — keeps you under free-tier rate limits")
    args = ap.parse_args()

    # Validate environment *before* importing modules that build a Gemini client.
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("Set GEMINI_API_KEY first (free key at https://aistudio.google.com).")
    if not os.path.exists(args.pdf):
        sys.exit(f"BRSR PDF not found at '{args.pdf}'. Set BRSR_PDF or place brsr.pdf in repo root.")

    from raga import load_and_chunk_pdf, build_vector_store, search_documents, ask_priya_rag
    from evals.judge import judge_faithfulness

    print("Building BRSR vector store (one-time)...")
    chunks = load_and_chunk_pdf(args.pdf)
    collection, embedder = build_vector_store(chunks)

    cases = load_cases(args.max)
    rows = []

    for i, case in enumerate(cases, 1):
        if i > 1 and args.sleep:
            time.sleep(args.sleep)  # pace calls to respect free-tier rate limits
        q, kind = case["question"], case["type"]
        print(f"\n[{i}/{len(cases)}] ({kind}) {q}")
        row = {"id": case.get("id", f"case_{i}"), "type": kind, "question": q}
        try:
            context = "\n\n---\n\n".join(search_documents(q, collection, embedder))
            answer = with_retry(ask_priya_rag, q, collection, embedder)
            did_refuse = refused(answer)
            row.update(refused=did_refuse, answer=answer)

            if kind == "out_of_scope":
                row["correct_refusal"] = did_refuse
                print(f"   refused: {did_refuse}  -> {'PASS' if did_refuse else 'FAIL (hallucinated)'}")
            else:  # answerable
                row["answered"] = not did_refuse
                if did_refuse:
                    row["faithfulness"] = None
                    print("   over-refused on an answerable question -> FAIL")
                else:
                    verdict = with_retry(judge_faithfulness, q, context, answer)
                    row["verdict"] = verdict["verdict"]
                    row["faithfulness"] = FAITH_SCORE.get(verdict["verdict"], 0.0)
                    row["cited"] = has_citation(answer)
                    row["coverage"] = coverage(answer, case.get("must_mention"))
                    print(f"   verdict: {verdict['verdict']}  cited: {row['cited']}  coverage: {row['coverage']}")
                    if verdict["verdict"] != "SUPPORTED" and verdict.get("unsupported_claims"):
                        print(f"     unsupported: {verdict['unsupported_claims']}")
        except Exception as e:  # noqa: BLE001 — record & continue so one failure isn't fatal
            row["error"] = str(e)[:200]
            print(f"   ✗ skipped after retries: {e}")
        rows.append(row)

    # ---- Aggregate scorecard (errored cases excluded from denominators) ----
    errored = [r for r in rows if r.get("error")]
    answerable = [r for r in rows if r["type"] == "answerable" and not r.get("error")]
    oos = [r for r in rows if r["type"] == "out_of_scope" and not r.get("error")]
    answered = [r for r in answerable if r.get("answered")]
    faith_scores = [r["faithfulness"] for r in answered if r.get("faithfulness") is not None]
    mean_faith = sum(faith_scores) / len(faith_scores) if faith_scores else 0.0
    cited = [r for r in answered if r.get("cited")]
    fully_supported = [r for r in answered if r.get("verdict") == "SUPPORTED"]
    correct_refusals = [r for r in oos if r.get("correct_refusal")]

    print("\n" + "=" * 56)
    print(" FAITHFULNESS EVAL — Raga (BRSR RAG)")
    print("=" * 56)
    print(f" Cases: {len(rows)}  ({len(answerable)} answerable, {len(oos)} out-of-scope)")
    if errored:
        print(f" Skipped (API errors):              {len(errored)}  (try a larger --sleep)")
    print("\n Answerable:")
    print(f"   Answer rate (didn't over-refuse): {pct(len(answered), len(answerable))}")
    print(f"   Fully grounded (LLM-judge):       {pct(len(fully_supported), len(answered))}")
    print(f"   Mean faithfulness score:          {mean_faith:.2f}")
    print(f"   Citation present:                 {pct(len(cited), len(answered))}")
    print("\n Out-of-scope:")
    print(f"   Correct refusals:                 {pct(len(correct_refusals), len(oos))}")
    print("=" * 56)

    out = Path(__file__).parent / "results.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nPer-case results (with judge reasoning) written to {out}")


if __name__ == "__main__":
    main()
