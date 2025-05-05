# dashboard-admin/backend/analytics/Dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell’analytics
COPY . .

# Espone la porta 8000 internamente
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
