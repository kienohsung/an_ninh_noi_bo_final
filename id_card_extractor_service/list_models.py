import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try to find .env manually if not found
    if os.path.exists(".env"):
        print("Loading .env manually...")
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    api_key = line.strip().split("=", 1)[1].strip().strip('"')
                    break

if not api_key:
    print("No API Key found.")
else:
    genai.configure(api_key=api_key)
    print("Listing available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
