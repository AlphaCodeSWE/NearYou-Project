# services/message_generator/app.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langchain import PromptTemplate

# --------------- Configuration -----------------
PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
BASE_URL = os.getenv("OPENAI_API_BASE") or None  # e.g. https://api.groq.com/openai/v1
API_KEY = os.getenv("GROQ_API_KEY")              # il tuo token Groq Cloud

# Verifica configurazione corretta
if PROVIDER != "groq":
    raise RuntimeError("LLM_PROVIDER deve essere impostato a 'groq'.")
if not API_KEY:
    raise RuntimeError("Manca la variabile GROQ_API_KEY: inserisci il token Groq Cloud come secret in GitHub/Gitpod.")

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
template = PromptTemplate(
    input_variables=["age", "profession", "interests", "name", "category", "description"],
    template=PROMPT_TMPL,
)

# --------------- LLM Invocation -----------------
def call_llm(prompt: str) -> str:
    # Modello Groq Cloud
    model_name = "gemma2-9b-it"
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.7,
        openai_api_key=API_KEY,
        openai_api_base=BASE_URL,
    )
    return llm([HumanMessage(content=prompt)]).content.strip()

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

app = FastAPI(title="NearYou Message Generator")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    try:
        prompt_text = template.format(
            age=req.user.age,
            profession=req.user.profession,
            interests=req.user.interests,
            name=req.poi.name,
            category=req.poi.category,
            description=req.poi.description,
        )
        result = call_llm(prompt_text)
        return GenerateResponse(message=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


