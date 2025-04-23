# services/message_generator/app.py

import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- Configurazione HF Inference API ---
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # definisci questo in .env
HF_MODEL       = os.getenv("HF_MODEL", "gpt2")  # es. "gpt2", "distilgpt2", o un modello più grande se hai quota

if not HF_API_TOKEN:
    raise RuntimeError("HF_API_TOKEN mancante per l'API di Hugging Face")

HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}


# --------------- Prompt Template -----------------
PROMPT_TMPL = """Sei un sistema di advertising che crea un messaggio conciso e coinvolgente.
Utente:
- Età: {age}
- Professione: {profession}
- Interessi: {interests}

Negozio:
- Nome: {name}
- Categoria: {category}
- Descrizione aggiuntiva: {description}

Condizioni:
- L'utente è a pochi metri dal negozio.
- Il messaggio deve essere breve (max 30 parole) e invogliare l'utente a fermarsi.

Genera il messaggio in italiano:"""


# --- Vecchia parte LangChain / Groq / OpenAI (commentata) ---
# from langchain.chat_models import ChatOpenAI
# from langchain.schema import HumanMessage
# PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
# BASE_URL = os.getenv("OPENAI_API_BASE") or None
# API_KEY  = os.getenv("OPENAI_API_KEY")
# if PROVIDER in {"openai", "groq"} and not API_KEY:
#     raise RuntimeError("OPENAI_API_KEY mancante")
#
# def call_llm_with_groq_or_openai(prompt: str) -> str:
#     model_name = "gpt-4o-mini" if PROVIDER == "openai" else "gemma2-9b-it"
#     llm = ChatOpenAI(
#         model=model_name,
#         temperature=0.7,
#         openai_api_key=API_KEY,
#         openai_api_base=BASE_URL,
#     )
#     return llm([HumanMessage(content=prompt)]).content.strip()


def call_llm(prompt: str) -> str:
    """
    Genera completamento tramite API di Hugging Face.
    """
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 50, "return_full_text": True},
    }
    resp = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
    if not resp.ok:
        raise HTTPException(status_code=502, detail=f"HF API error: {resp.status_code} {resp.text}")
    data = resp.json()
    # data può essere: {"generated_text": "..."} oppure [{"generated_text": "..."}]
    if isinstance(data, list):
        text = data[0].get("generated_text", "")
    else:
        text = data.get("generated_text", "")
    # togliamo il prompt iniziale
    return text[len(prompt):].strip()


# --------------- FastAPI App -----------------
class User(BaseModel):
    age: int
    profession: str
    interests: str

class POI(BaseModel):
    name: str
    category: str
    description: str = ""

class GenerateRequest(BaseModel):
    user: User
    poi: POI

class GenerateResponse(BaseModel):
    message: str

app = FastAPI(title="NearYou Message Generator (HF)")

@app.get("/health")
async def health():
    return {"status": "ok"}

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
