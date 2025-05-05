from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from models import admins
from security import create_access_token

app = FastAPI()

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = admins.get(form_data.username)
    if not user or user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}
