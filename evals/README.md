# 🔬 Faithfulness Eval — Raga (BRSR RAG)

Turns *"is this answer trustworthy?"* into numbers.

Raga answers BRSR questions **only** from the SEBI circular. This suite measures the two failure modes that actually matter in a regulated domain:

1. **Hallucination on answerable questions** — does the answer stay grounded in the retrieved excerpts?
2. **Over-confidence on out-of-scope questions** — does Raga *refuse* when the answer isn't in the document, instead of guessing?

## Metrics

| Metric | Measures | How |
|--------|----------|-----|
| **Answer rate** | Raga answers what it *should* (no over-refusing) | refusal-string match |
| **Faithfulness** | every claim in the answer is supported by the retrieved context | **LLM-as-judge** (Gemini, temp 0) → `SUPPORTED` / `PARTIAL` / `UNSUPPORTED` |
| **Citation present** | the answer cites a page / section | regex |
| **Correct refusals** | out-of-scope questions are declined, not hallucinated | refusal-string match |

Faithfulness is scored `SUPPORTED=1.0`, `PARTIAL=0.5`, `UNSUPPORTED=0.0` and averaged. The judge sees the **same retrieved context** the model saw, so this isolates *generation* faithfulness from *retrieval* quality.

## Run

```bash
export GEMINI_API_KEY="..."                 # free at https://aistudio.google.com
python -m evals.faithfulness_eval           # full suite (12 cases)
python -m evals.faithfulness_eval --max 4   # quick smoke test
```

Per-case results — including the judge's reasoning and any unsupported claims — are written to `evals/results.json` (commit it as evidence if you like).

## Example output *(illustrative — run it to get your real numbers)*

```
========================================================
 FAITHFULNESS EVAL — Raga (BRSR RAG)
========================================================
 Cases: 12  (8 answerable, 4 out-of-scope)

 Answerable:
   Answer rate (didn't over-refuse): 8/8 (100%)
   Fully grounded (LLM-judge):       7/8 (88%)
   Mean faithfulness score:          0.94
   Citation present:                 8/8 (100%)

 Out-of-scope:
   Correct refusals:                 4/4 (100%)
========================================================
```

## Design notes & limitations

- **LLM-as-judge** is the standard way to grade free-text faithfulness, but it isn't infallible — use `gemini-2.5-pro` as the judge (`JUDGE_MODEL` in [`judge.py`](judge.py)) for higher fidelity, and spot-check `results.json`.
- `must_mention` keyword coverage is a cheap lexical signal, **secondary** to the judge verdict.
- The dataset is small and hand-written — a starting point, not a benchmark. Grow it with adversarial / edge-case questions and near-misses (questions *partially* covered by the document).
