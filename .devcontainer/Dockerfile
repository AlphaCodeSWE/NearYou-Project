FROM python:3.10-slim

# Aggiorna gli indici dei pacchetti e installa il client Docker
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

# Imposta la directory di lavoro
WORKDIR /workspace

# Assicurati che lo script di inizializzazione abbia i permessi di esecuzione
RUN chmod +x .devcontainer/scripts/init_clickhouse.sh

# Mantieni il container in esecuzione
CMD ["sleep", "infinity"]
