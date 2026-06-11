"""LLM-as-judge for faithfulness scoring.

Uses Gemini (the same provider as the app) as a strict grader: given the
retrieved CONTEXT and Raga's ANSWER, decide whether every claim in the answer is
actually supported by the context. The judge runs at temperature 0 for
determinism and returns a structured verdict.
"""
import os
import json

from google import genai
from google.genai import types

# A stronger model makes a better judge; flash keeps it cheap and matches the
# app. Swap to "models/gemini-2.5-pro" for higher-fidelity grading.
JUDGE_MODEL = "models/gemini-2.5-flash"

JUDGE_SYSTEM = """You are a strict evaluation judge for a retrieval-augmented
generation system used in regulatory compliance. Decide whether an ANSWER is
fully grounded in the provided CONTEXT: every factual claim — including any page
numbers or section references — must be directly supported by the context.
Be skeptical. An answer that invents facts or citations is NOT supported."""

_client = None


def _get_client():
    """Construct the Gemini client lazily so importing this module never fails."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def judge_faithfulness(question: str, context: str, answer: str) -> dict:
    """Return {"verdict": SUPPORTED|PARTIAL|UNSUPPORTED, "unsupported_claims": [...], "reasoning": "..."}."""
    prompt = f"""
<context>
{context}
</context>

<question>
{question}
</question>

<answer>
{answer}
</answer>

<task>
Is every factual claim in the ANSWER supported by the CONTEXT?
Return ONLY valid JSON, no markdown:
{{
  "verdict": "SUPPORTED | PARTIAL | UNSUPPORTED",
  "unsupported_claims": ["any claims not found in the context"],
  "reasoning": "one short sentence"
}}
</task>
"""
    resp = _get_client().models.generate_content(
        model=JUDGE_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=JUDGE_SYSTEM,
            temperature=0,
        ),
        contents=prompt,
    )
    raw = resp.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "verdict": "PARTIAL",
            "unsupported_claims": [],
            "reasoning": f"judge returned non-JSON: {raw[:120]}",
        }

    # Normalise the verdict to one of the three allowed labels.
    v = str(data.get("verdict", "")).upper()
    data["verdict"] = next(
        (x for x in ("SUPPORTED", "PARTIAL", "UNSUPPORTED") if x in v), "PARTIAL"
    )
    data.setdefault("unsupported_claims", [])
    data.setdefault("reasoning", "")
    return data
