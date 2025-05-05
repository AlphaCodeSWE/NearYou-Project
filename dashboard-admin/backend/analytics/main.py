from fastapi import FastAPI
from .router import router

app = FastAPI(title="Admin Analytics API")
app.include_router(router)
