import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


# --- DTOs ---
class AIRequest(BaseModel):
    specText: str
    prompt: str


class AIResponse(BaseModel):
    updatedSpecText: str


# --- Ollama Configuration ---
OLLAMA_URL = "http://localhost:11434/api/chat"


def build_prompt_messages(spec: str, request: str) -> list:
    # ... (this function remains the same)
    system_prompt = """You are an expert api document, api developer/architect who is my assistant. Your task is to modify the provided OpenAPI YAML specification based on the user's request.
You must only output the new, complete, and valid YAML specification. 
Do not add any commentary, explanations, or markdown fences like ```yaml."""
    user_prompt = f"""Here is the current specification:
<SPECIFICATION>
{spec}
</SPECIFICATION>

Here is the user's request:
<REQUEST>
{request}
</REQUEST>"""
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def extract_generated_text(response_json) -> str:
    """Extracts and cleans the content from an Ollama response."""
    try:
        raw_text = response_json['message']['content']

        # --- UPDATED CLEANUP LOGIC ---
        # Look for either the old or new tag format
        cleaned_text = raw_text
        if "<SPECIFICATION>" in cleaned_text:
            cleaned_text = cleaned_text.split("<SPECIFICATION>", 1)[1]
            cleaned_text = cleaned_text.split("</SPECIFICATION>", 1)[0]
        elif "<NEW_SPECIFICATION>" in cleaned_text:
            cleaned_text = cleaned_text.split("<NEW_SPECIFICATION>", 1)[1]
            cleaned_text = cleaned_text.split("</NEW_SPECIFICATION>", 1)[0]

        return cleaned_text.strip()

    except (KeyError, IndexError, TypeError):
        return "Error: Could not parse AI response from Ollama."


@app.post("/process", response_model=AIResponse)
def process_specification(request: AIRequest):
    # ... (this function remains the same)
    messages = build_prompt_messages(request.specText, request.prompt)
    payload = {
        "model": "mistral",
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2  # Add this to make the output less random
        }
    }
    response = requests.post(OLLAMA_URL, json=payload)
    if response.status_code == 200:
        generated_text = extract_generated_text(response.json())
        return AIResponse(updatedSpecText=generated_text)
    else:
        return AIResponse(updatedSpecText=f"Error from Ollama service: {response.status_code} - {response.text}")
