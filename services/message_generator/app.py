from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from transformers import pipeline, logging as hf_logging

# —– SETUP LOGGING —–
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("message-generator")
hf_logging.set_verbosity_error()

# —– PAYLOAD CLASSES —–
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

# —– PROMPT —–
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

# —– CARICAMENTO MODELLO MISTRAL-7B —–
logger.info("Caricamento modello Mistral-7B…")
text_gen = pipeline(
    "text-generation",
    model="mistralai/Mistral-7B-Instruct",    # repository su HF
    device_map="auto",                        # mappa su GPU/CPU automaticamente
    load_in_8bit=True,                        # quantizzazione 8-bit se supportata
    torch_dtype="auto",                       # sceglie il dtype migliore
    trust_remote_code=True                    # necessario per alcuni custom model
)

# —– FASTAPI SETUP —–
app = FastAPI(title="NearYou Mistral-7B Message Generator")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    prompt = PROMPT_TMPL.format(
        age=req.user.age,
        profession=req.user.profession,
        interests=req.user.interests,
        name=req.poi.name,
        category=req.poi.category,
        description=req.poi.description or "-"
    )
    try:
        out = text_gen(
            prompt,
            max_new_tokens=40,
            do_sample=False,
            num_beams=4,
            early_stopping=True,
            return_full_text=False
        )
        message = out[0]["generated_text"].strip()
        return GenerateResponse(message=message)
    except Exception as e:
        logger.exception("Errore generazione con Mistral")
        raise HTTPException(status_code=500, detail="Errore interno al server")
