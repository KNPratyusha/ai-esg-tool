import os
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brsr_assistant.ai_client import generate

EXTRACTOR_PROMPT = """You are an ESG data extraction specialist. Your job is to 
extract structured ESG data from company reports with precision.

RULES:
- Extract ONLY what is explicitly stated in the report
- Never infer or assume values not mentioned
- Use null for any data point not mentioned
- All emissions in tCO2e
- All energy in kWh
- All waste in metric tonnes
- Numbers as numbers, not strings"""

def extract_company_esg(report_text):
    """
    Extracts structured ESG data from a company report.
    Returns a dictionary of all ESG data points found.
    """
    
    prompt = f"""
<company_report>
{report_text}
</company_report>

<task>
Extract all ESG data from this report. Return ONLY valid JSON.
No explanation. No markdown. Just the JSON object.
</task>

<output_format>
{{
  "company_name": null,
  "reporting_year": null,
  "location": null,
  
  "environmental": {{
    "energy_total_kwh": null,
    "energy_renewable_kwh": null,
    "energy_renewable_percent": null,
    "scope1_emissions_tco2e": null,
    "scope2_emissions_tco2e": null,
    "scope3_emissions_tco2e": null,
    "water_withdrawal_kl": null,
    "water_discharge_kl": null,
    "total_waste_processed_mt": null,
    "waste_recovered_mt": null,
    "waste_recovery_percent": null,
    "waste_to_landfill_mt": null,
    "hazardous_waste_mt": null,
    "diesel_consumed_litres": null,
    "environmental_fines": null,
    "has_eia_conducted": null,
    "biodiversity_assessment": null
  }},
  
  "social": {{
    "total_employees": null,
    "informal_workers_formalised": null,
    "lost_time_injuries": null,
    "fatalities": null,
    "avg_training_hours": null,
    "has_epf_esi": null,
    "has_health_insurance": null,
    "has_grievance_mechanism": null,
    "child_labor_policy": null,
    "forced_labor_policy": null
  }},
  
  "governance": {{
    "has_sustainability_policy": null,
    "has_board_esg_oversight": null,
    "has_standalone_esg_report": null,
    "third_party_verified": null,
    "anti_corruption_policy": null,
    "whistleblower_mechanism": null,
    "brsr_reported_previously": null
  }},
  
  "data_quality": {{
    "completeness_percent": null,
    "fields_reported": null,
    "fields_missing": null
  }}
}}
</output_format>
"""

    raw = generate(prompt, EXTRACTOR_PROMPT).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(raw)
        
        # Calculate completeness
        env = data.get("environmental", {})
        soc = data.get("social", {})
        gov = data.get("governance", {})
        
        all_fields = list(env.values()) + list(soc.values()) + list(gov.values())
        reported = [f for f in all_fields if f is not None]
        
        data["data_quality"] = {
            "completeness_percent": round(len(reported) / len(all_fields) * 100),
            "fields_reported": len(reported),
            "fields_missing": len(all_fields) - len(reported)
        }
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw: {raw[:200]}")
        return None


def load_report_from_file(filepath):
    """Loads report text from a .txt or .pdf file"""
    if filepath.endswith(".txt"):
        with open(filepath, "r") as f:
            return f.read()
    elif filepath.endswith(".pdf"):
        import fitz
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    else:
        raise ValueError("Unsupported file format. Use .txt or .pdf")


if __name__ == "__main__":
    # Test with sample report
    print("Loading sample company report...")
    report = load_report_from_file("brsr_assistant/sample_company_report.txt")
    
    print("Extracting ESG data...")
    data = extract_company_esg(report)
    
    if data:
        print("\n" + "="*60)
        print("EXTRACTED ESG DATA")
        print("="*60)
        print(json.dumps(data, indent=2))
        
        dq = data.get("data_quality", {})
        print(f"\nData completeness: {dq.get('completeness_percent')}%")
        print(f"Fields reported: {dq.get('fields_reported')}")
        print(f"Fields missing: {dq.get('fields_missing')}")

