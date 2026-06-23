import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

test_models = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash-lite-001",
    "gemini-2.0-flash-001",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-flash-latest"
]

for m in test_models:
    try:
        print(f"\nTesting {m}...")
        response = client.models.generate_content(
            model=m,
            contents="Hi"
        )
        print(f"SUCCESS: {m} -> {response.text}")
    except Exception as e:
        print(f"FAILED: {m} -> {e}")

