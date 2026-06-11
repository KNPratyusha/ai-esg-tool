import os
import json
import sys
import chromadb
import fitz
from sentence_transformers import SentenceTransformer
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brsr_assistant.ai_client import generate


ANALYSER_PROMPT = """You are Raga, a BRSR compliance specialist. You analyse 
companies' ESG data against official BRSR requirements from the SEBI circular.

RULES:
- Base your analysis ONLY on the BRSR document excerpts provided
- Always cite the specific page number from the BRSR document
- Be specific about what is missing and what is required
- Categorise each gap as: CRITICAL, IMPORTANT, or MINOR
- CRITICAL: mandatory disclosure completely missing
- IMPORTANT: disclosure present but incomplete
- MINOR: leadership indicator missing (voluntary)"""

# Load BRSR into vector store (reuse Raga from Day 3)
def load_brsr_vectorstore():
    brsr_path = os.environ.get("BRSR_PDF", "brsr.pdf")
    if not os.path.exists(brsr_path):
        raise FileNotFoundError(
            f"BRSR PDF not found at '{brsr_path}'. "
            "Place brsr.pdf in the repo root or set the BRSR_PDF environment variable."
        )

    print("Loading BRSR document...")
    doc = fitz.open(brsr_path)
    full_text = ""
    for page_num, page in enumerate(doc):
        full_text += f"\n[Page {page_num + 1}]\n{page.get_text()}"
    
    words = full_text.split()
    chunks = []
    chunk_size, overlap = 500, 50
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    chroma_client = chromadb.Client()
    
    try:
        chroma_client.delete_collection("brsr")
    except:
        pass
    
    collection = chroma_client.create_collection("brsr")
    embeddings = embedder.encode(chunks).tolist()
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )
    
    print(f"BRSR loaded: {len(chunks)} chunks")
    return collection, embedder


def check_requirement(requirement, company_data, collection, embedder):
    """
    Checks one BRSR requirement against company data.
    Returns gap analysis for that requirement.
    """
    # Search BRSR for this requirement
    query_emb = embedder.encode([requirement]).tolist()
    results = collection.query(query_embeddings=query_emb, n_results=3)
    brsr_context = "\n\n".join(results["documents"][0])
    
    prompt = f"""
<brsr_requirements>
{brsr_context}
</brsr_requirements>

<company_data>
{json.dumps(company_data, indent=2)}
</company_data>

<requirement_to_check>
{requirement}
</requirement_to_check>

<task>
Check if the company has met this BRSR requirement.
Return ONLY valid JSON. No markdown.
</task>

<output_format>
{{
  "requirement": "{requirement}",
  "status": "COMPLETE/INCOMPLETE/MISSING",
  "severity": "CRITICAL/IMPORTANT/MINOR",
  "what_company_reported": "what they have or null",
  "what_brsr_requires": "exact requirement from document",
  "brsr_page": "page number",
  "gap_description": "specific description of the gap",
  "remediation": "specific action to fix this"
}}
</output_format>
"""
    
    raw = generate(prompt, ANALYSER_PROMPT).strip().replace("```json","").replace("```","").strip()
    try:
        return json.loads(raw)
    except:
        return None


def run_gap_analysis(company_data):
    """
    Runs full BRSR gap analysis on extracted company data.
    """
    collection, embedder = load_brsr_vectorstore()
    
    # Key BRSR requirements to check
    requirements = [
        "Scope 1 and Scope 2 GHG emissions reporting requirement",
        "Water withdrawal and discharge reporting by source and destination",
        "Waste generated from operations and disposal methods",
        "Occupational health and safety incident reporting and LTIFR",
        "Employee wellbeing benefits EPF ESI health insurance",
        "Energy consumption from renewable and non-renewable sources",
        "Environmental compliance fines and penalties disclosure",
        "Standalone sustainability report or integrated reporting",
        "Anti-corruption policy and whistleblower mechanism",
        "Value chain partner environmental assessment"
    ]
    
    print(f"\nChecking {len(requirements)} BRSR requirements...")
    gaps = []
    
    for i, req in enumerate(requirements):
        print(f"  Checking {i+1}/{len(requirements)}: {req[:50]}...")
        result = check_requirement(req, company_data, collection, embedder)
        if result:
            gaps.append(result)
    
    return gaps


if __name__ == "__main__":
    # Import extractor
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from brsr_assistant.extractor import extract_company_esg, load_report_from_file
    
    # Load and extract company data
    report = load_report_from_file("brsr_assistant/sample_company_report.txt")
    company_data = extract_company_esg(report)
    
    # Run gap analysis
    gaps = run_gap_analysis(company_data)
    
    print("\n" + "="*60)
    print("GAP ANALYSIS RESULTS")
    print("="*60)
    print(json.dumps(gaps, indent=2))