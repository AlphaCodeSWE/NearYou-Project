# .devcontainer/Dockerfile
FROM python:3.10-slim

# Aggiorna gli indici dei pacchetti e installa il client Docker
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

# Imposta la directory di lavoro
WORKDIR /workspace

# Copia il file delle dipendenze e installa i pacchetti Python necessari
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia la cartella degli script dall'host all'interno dell'immagine
# Il contesto di build è la radice del repository (NearYou-Project)
COPY . /workspace         
COPY .devcontainer/scripts /workspace/.devcontainer/scripts

# Imposta i permessi di esecuzione per lo script di inizializzazione
RUN chmod +x /workspace/.devcontainer/scripts/init_clickhouse.sh

# Mantieni il container in esecuzione (come default)
CMD ["sleep", "infinity"]