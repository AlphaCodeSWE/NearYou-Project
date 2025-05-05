FROM python:3.10-slim

WORKDIR /app

# install delle dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# espone la porta WS
EXPOSE 8002


CMD ["uvicorn", "ws:app", "--host", "0.0.0.0", "--port", "8002"]
