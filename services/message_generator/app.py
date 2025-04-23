from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, requests, logging

# —– SETUP LOGGING —–
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("message-generator")

# —– HF CONFIG —–
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL     = os.getenv("HF_MODEL", "gpt2")
if not HF_API_TOKEN:
    logger.error("HF_API_TOKEN non trovato nelle env vars")
    raise RuntimeError("HF_API_TOKEN mancante per l'API di Hugging Face")

HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

logger.info(f"Hugging Face API URL: {HF_API_URL}")

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

# —– CALL HF —–
def call_llm(prompt: str) -> str:
    logger.info("Chiamata a Hugging Face API")
    logger.debug(f"Payload prompt: {prompt!r}")
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 50, "return_full_text": True}}
    resp = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
    logger.info(f"HF API response status: {resp.status_code}")
    if not resp.ok:
        logger.error(f"HF API error body: {resp.text}")
        raise HTTPException(status_code=502, detail=f"HF API error: {resp.status_code} {resp.text}")
    data = resp.json()
    logger.debug(f"HF API response JSON: {data}")
    text = data[0]["generated_text"] if isinstance(data, list) else data["generated_text"]
    completion = text[len(prompt):].strip()
    logger.info(f"Generated text (trimmed): {completion!r}")
    return completion

# —– FASTAPI SETUP —–
app = FastAPI(title="NearYou Message Generator (HF)")

@app.get("/health")
async def health():
    logger.info("Health check")
    return {"status": "ok"}

@app.get("/check-token")
async def check_token():
    logger.info("Token check endpoint")
    resp = requests.head(HF_API_URL, headers=HF_HEADERS, timeout=10)
    logger.info(f"Token check status: {resp.status_code}")
    if resp.status_code == 200:
        return {"hf_token_valid": True}
    else:
        raise HTTPException(status_code=502, detail=f"HF token non valido ({resp.status_code})")

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    logger.info(f"Generate request received: user={req.user} poi={req.poi}")
    try:
        prompt_text = PROMPT_TMPL.format(
            age=req.user.age,
            profession=req.user.profession,
            interests=req.user.interests,
            name=req.poi.name,
            category=req.poi.category,
            description=req.poi.description,
        )
        message = call_llm(prompt_text)
        return GenerateResponse(message=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Errore in /generate")
        raise HTTPException(status_code=500, detail=str(e))
