# dashboard-admin/backend/auth/Dockerfile

FROM python:3.10-slim

# 1) Dipendenze di sistema necessarie per bcrypt/passlib
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libssl-dev \
      libffi-dev \
      python3-dev \
 && rm -rf /var/lib/apt/lists/*

# 2) Cartella di lavoro
WORKDIR /app

COPY dashboard-admin/backend/auth/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY dashboard-admin/backend/auth/ /app


EXPOSE 8002

# 6) Avvio Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
