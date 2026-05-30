AI ESG Tool — Priya & Raga

An AI-powered ESG compliance assistant built for Indian companies and NGOs.


PROJECTS

1. ESG Domain Specialist (first_gemini_call.py)
   Asks Gemini for GRI guidance for Indian waste management companies.

2. Priya — Interactive ESG Analyst (prompt_engineering.py)
   A named ESG specialist. Answers any ESG question, extracts structured
   JSON data from sustainability reports, and flags compliance gaps.

3. Raga — Document-Grounded Compliance Tool (raga.py)
   Answers BRSR compliance questions directly from the official SEBI circular.
   Every answer cites the exact page number. No hallucination. Full traceability.
   Built with ChromaDB, sentence-transformers, and Gemini.


TECH STACK

- Python 3.14
- Google Gemini API (google-genai)
- ChromaDB, Sentence Transformers, PyMuPDF
- GRI / SASB / BRSR domain knowledge


SETUP

1. Clone the repo
   git clone https://github.com/KNPratyusha/ai-esg-tool.git
   cd ai-esg-tool

2. Activate virtual environment
   python3 -m venv venv
   source venv/bin/activate

3. Install dependencies
   pip3 install google-genai chromadb pymupdf sentence-transformers

4. Set your Gemini API key (free at aistudio.google.com)
   export GEMINI_API_KEY="your-key-here"

5. Run
   python3 first_gemini_call.py
   python3 prompt_engineering.py
   python3 raga.py
