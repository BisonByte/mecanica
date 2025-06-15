# Simple Dockerfile for the web simulator
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY simulador_viga_mejorado.py ./
COPY frontend ./frontend

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
