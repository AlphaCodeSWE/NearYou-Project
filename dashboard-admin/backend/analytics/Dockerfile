FROM python:3.10-slim

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia il codice
COPY . /app

# espone il servizio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
