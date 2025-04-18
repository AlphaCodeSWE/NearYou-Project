import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langchain import PromptTemplate

# ---------- configurazione provider ----------
PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
BASE_URL = os.getenv("OPENAI_API_BASE") or None
API_KEY  = os.getenv("OPENAI_API_KEY")          # usata da Groq/Together/Fireworks/OpenAI

if PROVIDER in {"openai", "groq", "together", "fireworks"} and not API_KEY:
    raise RuntimeError("OPENAI_API_KEY mancante per il provider scelto")

# ---------- prompt template ----------
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
template = PromptTemplate(
    input_variables=["age", "profession", "interests",
                     "name", "category", "description"],
    template=PROMPT_TMPL,
)

# ---------- helper per chiamare il modello ----------
def call_llm(prompt: str) -> str:
    # Provider con API compatibile OpenAI (Groq è qui)
    if PROVIDER in {"openai", "groq", "together", "fireworks"}:
        llm = ChatOpenAI(
            model="mixtral-8x7b-32768" if PROVIDER != "openai" else "gpt-4o-mini",
            temperature=0.7,
            openai_api_key=API_KEY,
            openai_api_base=BASE_URL,
        )
        return llm([HumanMessage(content=prompt)]).content.strip()

    raise RuntimeError(f"Provider LLM non supportato: {PROVIDER}")

# ---------- FastAPI ----------
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

app = FastAPI(title="NearYou Message Generator")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    try:
        prompt = template.format(
            age=req.user.age,
            profession=req.user.profession,
            interests=req.user.interests,
            name=req.poi.name,
            category=req.poi.category,
            description=req.poi.description,
        )
        result = call_llm(prompt)
        return GenerateResponse(message=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
