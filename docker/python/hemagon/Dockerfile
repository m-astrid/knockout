FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir playwright && \
    playwright install chromium && \
    playwright install-deps

COPY python/hemagon/ /app/

RUN pip install --no-cache-dir fastapi uvicorn[standard] playwright requests

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]