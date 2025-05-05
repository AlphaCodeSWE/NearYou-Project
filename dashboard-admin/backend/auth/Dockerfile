
FROM python:3.10-slim


WORKDIR /app


RUN pip install --no-cache-dir fastapi uvicorn python-jose[cryptography]


COPY dashboard-admin/backend/auth/ /app

# expone la porta di default
EXPOSE 8002


CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
