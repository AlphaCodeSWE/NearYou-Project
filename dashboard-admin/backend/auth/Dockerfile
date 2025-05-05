# dashboard-admin/backend/auth/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# installa solo le dipendenze di auth
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia il codice
COPY . .

EXPOSE 8002
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
