# dashboard-admin/backend/auth/Dockerfile

FROM python:3.10-slim

# installa i dev headers e tools per bcrypt/passlib
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libssl-dev \
      libffi-dev \
      python3-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copia e installa le dipendenze
COPY dashboard-admin/backend/auth/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# copia il codice dell’auth service
COPY dashboard-admin/backend/auth/ /app

EXPOSE 8002

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
