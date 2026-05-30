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

sample_report = """
Our company generated 2,400 metric tonnes of waste during FY2023-24.
Of this, 1,800 MT was recycled, a 75% recovery rate.
Our 65 vehicles consumed 180,000 litres of diesel.
We recorded 12 Lost Time Injuries. We have 380 employees.
"""

print("=== Asking Priya ===")
print(ask_priya("What is BRSR and why should a waste management company care?"))

print("\n=== ESG Data Extraction ===")
result = extract_esg_data(sample_report)
if result:
    print(json.dumps(result, indent=2))