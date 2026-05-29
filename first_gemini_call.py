from google import genai
import os

API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="models/gemini-2.0-flash-lite",
    contents="A mid-sized waste management company in India wants to start ESG reporting. Which GRI Standards should they prioritise and why?"
)

print(response.text)