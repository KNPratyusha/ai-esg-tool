# AI ESG Tool

An AI-powered ESG analysis assistant built on Google Gemini, designed to help
Indian companies and NGOs navigate sustainability reporting frameworks including
GRI, SASB, BRSR, and GHG accounting.


WHAT IT DOES

Ask it anything about ESG reporting and it responds as a domain expert —
citing specific standard numbers, explaining materiality, and giving
India-specific guidance that generic AI tools miss.


WHY I BUILT THIS

I spent 3 years doing ground-level sustainability work in India — waste audits
with Recykal, ESG assessments at Uniqus Consultech, field visits to 2000+
household communities in Bengaluru. I know the gap that exists between
international frameworks and what Indian companies actually need.

This tool is the beginning of bridging that gap with AI.


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

5. Run
   python3 first_gemini_call.py


EXAMPLE OUTPUT

Query: "A mid-sized waste management company in India wants to start ESG
reporting. Which GRI Standards should they prioritise and why?"

Returns a structured breakdown covering GRI Universal Standards, GRI 305
Emissions, GRI 306 Waste, GRI 403 Occupational Health and Safety, GRI 413
Local Communities, and India-specific context including informal sector
integration and Plastic Waste Management Rules.

