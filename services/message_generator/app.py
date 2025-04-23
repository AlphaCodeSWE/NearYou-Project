import os
import requests
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

# --- Configurazione HF Inference API ---
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL     = os.getenv("HF_MODEL", "gpt2")

if not HF_API_TOKEN:
    raise RuntimeError("HF_API_TOKEN mancante per l'API di Hugging Face")

HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}


# --------------- Prompt Template -----------------
PROMPT_TMPL = """Sei un sistema di advertising che crea un messaggio conciso e coinvolgente.
...
Genera il messaggio in italiano:"""


def call_llm(prompt: str) -> str:
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 50, "return_full_text": True},
    }
    resp = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
    if not resp.ok:
        raise HTTPException(status_code=502,
                            detail=f"HF API error: {resp.status_code} {resp.text}")
    data = resp.json()
    if isinstance(data, list):
        text = data[0].get("generated_text", "")
    else:
        text = data.get("generated_text", "")
    return text[len(prompt):].strip()


# --------------- FastAPI App -----------------
app = FastAPI(title="NearYou Message Generator (HF)")

@app.get("/check-token")
async def check_token():
    """
    Verifica che il token HF sia stato caricato.
    """
    if not HF_API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="HF_API_TOKEN non impostato")
    return {"status": "token OK"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# ... qui tutte le classi Pydantic ...

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    try:
        prompt_text = PROMPT_TMPL.format(
            age=req.user.age,
            profession=req.user.profession,
            interests=req.user.interests,
            name=req.poi.name,
            category=req.poi.category,
            description=req.poi.description,
        )
        result = call_llm(prompt_text)
        return GenerateResponse(message=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
