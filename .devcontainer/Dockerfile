# .devcontainer/Dockerfile

FROM python:3.10-slim

# 1) Installazione tool di sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      docker.io \               # client Docker (dind in devcontainer)
      git \                     # per scaricare modelli se necessario
      build-essential \         # gcc, make (per compilare librerie Python)
      python3-dev \             # header Python
    && rm -rf /var/lib/apt/lists/*

# 2) Directory di lavoro
WORKDIR /workspace

# 3) Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Pre‐scarica il modello gpt4all-j in cache per ridurre latency
RUN python3 - << 'EOF'
from gpt4all import GPT4All
# Questo download salva il modello in ~/.cache/gpt4all/
GPT4All(model="gpt4all-j")
print("Modello gpt4all-j pre‐scaricato.")
EOF

# 5) Copia tutto il codice del progetto
COPY . /workspace
COPY .devcontainer/scripts /workspace/.devcontainer/scripts

# 6) Rendi eseguibili gli script di init
RUN chmod +x \
      /workspace/.devcontainer/scripts/init_clickhouse.sh \
      /workspace/.devcontainer/scripts/init_postgres.sh \
      /workspace/.devcontainer/scripts/entrypoint.sh

# 7) Comando di default (mantieni il container vivo in dev)
CMD ["sleep", "infinity"]
