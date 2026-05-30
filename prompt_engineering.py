import os
import json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are Priya, an expert ESG analyst with 12 years of experience
advising Indian companies on sustainability reporting. You have deep knowledge of
GRI Standards, BRSR, SASB, GHG Protocol, and Indian environmental regulations.
Always cite specific standard numbers. Give India-specific examples.
Be direct and actionable."""

def ask_priya(question):
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        ),
        contents=question
    )
    return response.text

def extract_esg_data(report_text):
    prompt = f"""
<report_text>
{report_text}
</report_text>

<task>
Extract all ESG data points from this report and return as JSON only.
No explanation. No markdown. Just valid JSON.
</task>

<output_format>
{{
  "environmental": {{
    "total_waste_generated_mt": null,
    "waste_recovered_mt": null,
    "recovery_rate_percent": null,
    "diesel_consumed_litres": null
  }},
  "social": {{
    "total_employees": null,
    "lost_time_injuries": null
  }},
  "compliance_gaps": [],
  "overall_completeness": "Low/Medium/High"
}}
</output_format>
"""
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        ),
        contents=prompt
    )
    raw = response.text.strip().replace("```json","").replace("```","").strip()
    try:
        return json.loads(raw)
    except:
        print("Raw response:", raw)
        return None

# Show one example on first run so users know what to ask
print("\n=== Example (how to ask Priya) ===")
example_q = "What is BRSR and why should a waste management company care?"
print(f"You: {example_q}")
example_answer = ask_priya(example_q)
print(f"\nPriya: {example_answer}\n")
print("-" * 60)
print("That was an example. Now ask your own question below.")
print("-" * 60)

# Interactive mode
print("\n=== Ask Priya ===")
print("Type your ESG question and press Enter. Type 'quit' to exit.\n")

while True:
    question = input("You: ")
    if question.lower() == "quit":
        print("Goodbye!")
        break
    answer = ask_priya(question)
    print(f"\nPriya: {answer}\n")
