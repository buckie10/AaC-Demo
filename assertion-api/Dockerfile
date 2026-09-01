FROM python:3.12-slim
WORKDIR /app
COPY assertion-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY assertion-api/src ./src
COPY semantic/shapes.ttl /app/semantic/shapes.ttl
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
