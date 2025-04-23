# services/message_generator/app.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- Generazione locale con GPT4All ---
from gpt4all import GPT4All

# --------------- Configuration -----------------
# (le variabili PROVIDER, BASE_URL e API_KEY non servono più)
# PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()   # NON USATO
# BASE_URL = os.getenv("OPENAI_API_BASE") or None         # NON USATO
# API_KEY  = os.getenv("OPENAI_API_KEY")                  # NON USATO

# if PROVIDER in {"openai", "groq", "together", "fireworks"} and not API_KEY:
#     raise RuntimeError("OPENAI_API_KEY mancante per il provider scelto")

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

# --- RIMOSSO: LangChain PromptTemplate e template ---
# from langchain import PromptTemplate
# template = PromptTemplate(
#     input_variables=["age", "profession", "interests", "name", "category", "description"],
#     template=PROMPT_TMPL,
# )

# --------------- LLM Invocation -----------------
# Carica il modello GPT4All “j” (leggero, ~200 MB)
llm_local = GPT4All(model="gpt4all-j")

def call_llm(prompt: str) -> str:
    """
    Genera completamento locale con gpt4all-j.
    """
    # .generate restituisce prompt + completamento
    full_text = llm_local.generate(prompt, max_tokens=50)
    # Rimuove la parte di prompt, lasciando solo il completamento
    return full_text[len(prompt):].strip()

# --- RIMOSSO: chiamata a ChatOpenAI tramite LangChain/OpenAI API ---
# def call_llm(prompt: str) -> str:
#     if PROVIDER in {"openai", "groq", "together", "fireworks"}:
#         model_name = "gpt-4o-mini" if PROVIDER == "openai" else "gemma2-9b-it"
#         llm = ChatOpenAI(
#             model=model_name,
#             temperature=0.7,
#             openai_api_key=API_KEY,
#             openai_api_base=BASE_URL,
#         )
#         return llm([HumanMessage(content=prompt)]).content.strip()
#     raise RuntimeError(f"Provider LLM non supportato: {PROVIDER}")

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
        # Costruzione del prompt
        prompt_text = PROMPT_TMPL.format(
            age=req.user.age,
            profession=req.user.profession,
            interests=req.user.interests,
            name=req.poi.name,
            category=req.poi.category,
            description=req.poi.description,
        )
        # Generazione locale
        result = call_llm(prompt_text)
        return GenerateResponse(message=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
