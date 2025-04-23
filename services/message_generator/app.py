from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, requests

# —– HF CONFIG —–
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL     = os.getenv("HF_MODEL", "gpt2")
if not HF_API_TOKEN:
    raise RuntimeError("HF_API_TOKEN mancante per l'API di Hugging Face")
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

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
PROMPT_TMPL = """Sei un sistema di advertising ... Genera il messaggio in italiano:"""

# —– CALL HF —–
def call_llm(prompt: str) -> str:
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 50, "return_full_text": True}}
    resp = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
    if not resp.ok:
        raise HTTPException(status_code=502, detail=f"HF API error: {resp.status_code} {resp.text}")
    data = resp.json()
    text = data[0]["generated_text"] if isinstance(data, list) else data["generated_text"]
    return text[len(prompt):].strip()

# —– FASTAPI SETUP —–
app = FastAPI(title="NearYou Message Generator (HF)")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    prompt_text = PROMPT_TMPL.format(
        age=req.user.age,
        profession=req.user.profession,
        interests=req.user.interests,
        name=req.poi.name,
        category=req.poi.category,
        description=req.poi.description,
    )
    return GenerateResponse(message=call_llm(prompt_text))
