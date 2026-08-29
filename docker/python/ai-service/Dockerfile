FROM python:3.11-slim

WORKDIR /app

COPY python/ai-service/ /app/

RUN pip install --no-cache-dir fastapi uvicorn[standard] requests

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]