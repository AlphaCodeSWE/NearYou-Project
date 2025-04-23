# .devcontainer/Dockerfile
FROM python:3.10-slim

# 1) Aggiorna gli indici dei pacchetti e installa i tool di sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      docker.io \                # per docker-in-docker in devcontainer
      curl \                     # utile per healthchecks e test API
      postgresql-client \        # psql per connetterti a Postgres in dev
      build-essential \         # gcc, g++, make
      python3-dev \             # header Python per moduli compilati
      libssl-dev \              # per cryptography
      libffi-dev \              # per cryptography e altri wrapper FF
    && rm -rf /var/lib/apt/lists/*

# 2) Imposta la directory di lavoro
WORKDIR /workspace

# 3) Copia e installa le dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copia tutto il codice in /workspace
COPY . /workspace
COPY .devcontainer/scripts /workspace/.devcontainer/scripts

# 5) Imposta i permessi per gli script di inizializzazione
RUN chmod +x /workspace/.devcontainer/scripts/init_clickhouse.sh \
    /workspace/.devcontainer/scripts/init_postgres.sh \
    /workspace/.devcontainer/scripts/entrypoint.sh

# 6) Default command
CMD ["sleep", "infinity"]
