# dashboard-admin/backend/analytics/main.py

from fastapi import FastAPI
from router import router as analytics_router

app = FastAPI(title="Admin Analytics")
app.include_router(analytics_router)
