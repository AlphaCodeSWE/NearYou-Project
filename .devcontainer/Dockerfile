# .devcontainer/Dockerfile
FROM python:3.11-slim-bookworm

# Aggiorna gli indici dei pacchetti, installa docker.io e wget, poi pulisce la cache apt
RUN apt-get update \
 && apt-get install -y docker.io wget \
 && rm -rf /var/lib/apt/lists/*

# Imposta la directory di lavoro
WORKDIR /workspace

# Copia e installa le dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Scarica il modello GPT4All-J quantizzato (~200 MB)  
# in modo da averlo disponibile localmente e non doverlo scaricare a runtime.
RUN mkdir -p services/message_generator/models \
 && wget -q -O services/message_generator/models/ggml-gpt4all-j-v1.3-groovy.bin \
    https://huggingface.co/Sh1ree/ggml-gpt4all-j-v1.3-groovy/resolve/main/ggml-gpt4all-j-v1.3-groovy.bin

# Copia tutto il resto del progetto
COPY . /workspace
COPY .devcontainer/scripts /workspace/.devcontainer/scripts

# Rendi eseguibile lo script di init di ClickHouse
RUN chmod +x /workspace/.devcontainer/scripts/init_clickhouse.sh

# Default: tieni il container in vita
CMD ["sleep", "infinity"]
