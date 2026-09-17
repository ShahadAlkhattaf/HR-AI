FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn python-multipart pydantic

COPY . .

EXPOSE 8000

CMD ["uvicorn", "docker.api:app", "--host", "0.0.0.0", "--port", "8000"]