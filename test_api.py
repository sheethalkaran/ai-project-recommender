import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")
HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "inputs": "Translate English to French: Hello, how are you?",
    "parameters": { "max_new_tokens": 50 }
}

response = requests.post(HF_API_URL, headers=headers, json=payload)

print("Status Code:", response.status_code)
print("Response:", response.text)
