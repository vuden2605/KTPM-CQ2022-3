"""Script nhỏ để list các model Gemini có sẵn"""
import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY chưa được set!")
    exit(1)

client = genai.Client(api_key=api_key)

print("Danh sách models hỗ trợ:")
print("-" * 60)
for model in client.models.list():
    print(f"- {model.name}")
    if hasattr(model, 'supported_generation_methods'):
        print(f"  Methods: {model.supported_generation_methods}")
print("-" * 60)
