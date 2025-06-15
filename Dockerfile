# Simple Dockerfile for the web simulator
FROM python:3.11-slim

WORKDIR /app

COPY backend ./backend
COPY simulador_viga_mejorado.py ./
COPY frontend ./frontend

RUN pip install fastapi uvicorn[standard] numpy

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
