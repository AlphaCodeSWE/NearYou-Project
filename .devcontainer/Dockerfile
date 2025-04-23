# .devcontainer/Dockerfile
FROM python:3.11-slim-bookworm

# 1) Installa docker.io (se ti serve) e wget
RUN apt-get update \
 && apt-get install -y docker.io wget \
 && rm -rf /var/lib/apt/lists/*

# 2) Imposta la cartella di lavoro
WORKDIR /workspace

# 3) Copia requirements e installa le dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Crea la cartella per il modello e scaricalo
RUN mkdir -p services/message_generator/models \
 && wget -q -O services/message_generator/models/ggml-gpt4all-j-v1.3-groovy.bin \
    https://gpt4all.io/models/ggml-gpt4all-j-v1.3-groovy.bin

# 5) Copia tutto il progetto
COPY . /workspace
COPY .devcontainer/scripts /workspace/.devcontainer/scripts

# 6) Rendi eseguibile lo script di init di ClickHouse
RUN chmod +x /workspace/.devcontainer/scripts/init_clickhouse.sh

# 7) Default: tieni vivo il container
CMD ["sleep", "infinity"]
