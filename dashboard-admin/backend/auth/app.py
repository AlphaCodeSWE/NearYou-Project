from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from models import admin_user
from security import create_access_token, verify_token

app = FastAPI(title="Admin Auth Service")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if (form_data.username != admin_user["username"]
        or form_data.password != admin_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}

def get_current_admin(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload or payload.get("sub") != admin_user["username"]:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@app.get("/health")
async def health():
    return {"status": "ok"}

# endpoint di test protetto
@app.get("/me")
async def read_current_admin(_=Depends(get_current_admin)):
    return {"username": admin_user["username"]}
