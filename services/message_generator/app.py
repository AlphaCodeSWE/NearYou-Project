from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from transformers import pipeline, logging as hf_logging

# —– SETUP LOGGING —–
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("message-generator")
hf_logging.set_verbosity_error()  # silenzia i warning di transformers

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

# —– PROMPT TEMPLATE —–
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

# —– MODELLO SEQUENZIALE SU CPU —–
logger.info("Tentativo caricamento modello GGUF... (CPU)")
try:
    text_gen = pipeline(
        "text-generation",
        model="TheBloke/Mistral-7B-Instruct-GGUF",
        device_map="cpu",
        trust_remote_code=True
    )
    logger.info("Utilizzato modello GGUF su CPU")
except Exception:
    logger.warning("GGUF non disponibile, tentativo checkpoint GPTQ CPU...")
    try:
        text_gen = pipeline(
            "text-generation",
            model="TheBloke/Mistral-7B-Instruct-v0.1-AWQ",  # AWQ CPU variant
            device_map="cpu",
            trust_remote_code=True
        )
        logger.info("Utilizzato modello AWQ su CPU")
    except Exception:
        logger.warning("AWQ non disponibile, tentativo checkpoint GPTQ CPU...")
        try:
            text_gen = pipeline(
                "text-generation",
                model="TheBloke/Mistral-7B-Instruct-v0.1-GPTQ",
                device_map="cpu",
                trust_remote_code=True
            )
            logger.info("Utilizzato modello GPTQ su CPU")
        except Exception:
            logger.warning("GPTQ non disponibile, ricaduta su modello full (CPU, heavy)")
            text_gen = pipeline(
                "text-generation",
                model="TheBloke/Mistral-7B-Instruct-v0.1",
                device_map="cpu",
                torch_dtype="auto",
                trust_remote_code=True
            )
            logger.info("Utilizzato modello full su CPU")

# —– FASTAPI SETUP —–
app = FastAPI(title="NearYou Mistral-7B CPU Message Generator")

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
    logger.info(f"Prompt: {prompt!r}")
    try:
        out = text_gen(
            prompt,
            max_new_tokens=30,
            do_sample=False,
            num_beams=4,
            early_stopping=True,
            return_full_text=False
        )
        message = out[0]["generated_text"].strip()
        logger.info(f"Generated message: {message!r}")
        return GenerateResponse(message=message)
    except Exception:
        logger.exception("Errore generazione con modello CPU")
        raise HTTPException(status_code=500, detail="Errore interno al server")
