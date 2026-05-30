# AI ESG Tool

An AI-powered ESG analysis assistant built on Google Gemini, designed to help
Indian companies and NGOs navigate sustainability reporting frameworks including
GRI, SASB, BRSR, and GHG accounting.

WHY I BUILT THIS

I spent 3 years doing ground-level sustainability work in India — waste audits
with Recykal, ESG assessments at Uniqus Consultech, field visits to 2000+
household communities in Bengaluru. I know the gap between international
frameworks and what Indian companies actually need.

This tool is the beginning of bridging that gap with AI.

PROJECTS

1. ESG Domain Specialist (first_gemini_call.py)
   Ask any ESG question and get expert guidance citing specific GRI standard
   numbers, BRSR principles, and India-specific regulatory context.

2. Priya — ESG Analyst AI (prompt_engineering.py)
   A named ESG specialist built with advanced prompt engineering. Extracts
   structured ESG data from unstructured sustainability reports and returns
   clean JSON — emissions figures, waste recovery rates, compliance gaps.

TECH STACK

- Python 3.14
- Google Gemini API (google-genai)
- GRI / SASB / BRSR domain knowledge

SETUP

1. Clone the repo
   git clone https://github.com/KNPratyusha/ai-esg-tool.git
   cd ai-esg-tool

2. Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate

3. Install dependencies
   pip3 install google-genai

4. Set your Gemini API key (free at aistudio.google.com)
   export GEMINI_API_KEY="your-key-here"

5. Run any project
   python3 first_gemini_call.py
   python3 prompt_engineering.py

BACKGROUND

Built by Kanchi Pratyusha — 3 years of ground-level sustainability work
in India, now building AI tools for ESG and environmental impact.