# .devcontainer/Dockerfile
FROM python:3.10-slim

# 1) Installa tool di sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        docker.io \
        git \
        build-essential \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2) Imposta la directory di lavoro
WORKDIR /workspace

# 3) Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Pre-scarica il modello gpt4all-j in cache
RUN python3 - << 'EOF'
from gpt4all import GPT4All
GPT4All(model="gpt4all-j")
EOF

# 5) Copia il resto del progetto
COPY . /workspace
COPY .devcontainer/scripts /workspace/.devcontainer/scripts

# 6) Rendi eseguibili gli script di init
RUN chmod +x /workspace/.devcontainer/scripts/*.sh

# 7) Comando di default (mantiene vivo il container)
CMD ["sleep", "infinity"]
