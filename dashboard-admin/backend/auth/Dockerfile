# dashboard-admin/backend/auth/Dockerfile

FROM python:3.10-slim


RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

# 2) Imposta la cartella di lavoro
WORKDIR /app

COPY dashboard-admin/backend/auth/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copia tutto il codice di auth
COPY dashboard-admin/backend/auth/ /app

# 5) Espone la porta 8002
EXPOSE 8002

# 6) Avvia Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
