FROM python:3.12-slim

WORKDIR /app
COPY push_backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY push_backend ./push_backend

ENV PORT=8000
CMD ["sh", "-c", "uvicorn push_backend.app:app --host 0.0.0.0 --port ${PORT}"]
