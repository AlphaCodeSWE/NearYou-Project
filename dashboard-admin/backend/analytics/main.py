from fastapi import FastAPI
from router import router

app = FastAPI(
    title="Admin Analytics",
    description="API per statistiche e dati di dashboard-admin",
    version="0.1.0"
)

# include tutte le route definite in router.py
app.include_router(router, prefix="/analytics")
