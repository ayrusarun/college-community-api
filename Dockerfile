FROM dockerhub.paypalcorp.com/python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR and PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# copy over certificates
COPY --from=dockerhub.paypalcorp.com/developerexperience-r/paypal-certs:latest /paypal-certs/roots/* /usr/local/share/ca-certificates/
RUN update-ca-certificates

# Configure pip to use corporate certificates and PyPI mirror
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt
ENV PIP_TRUSTED_HOST=pypi.org,pypi.python.org,files.pythonhosted.org
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY ./app ./app
COPY db_setup.py .
COPY migrate_store.py .
COPY init_db.py .
COPY migrations ./migrations

# Performance: Optimized for 4 vCPU machine with burst loads
# --workers 4: One worker per vCPU core
# --loop uvloop: High-performance event loop (2-4x faster than asyncio)
# --limit-concurrency 250: Max 250 concurrent requests per worker (1000 total)
# --backlog 4096: Doubled queue size for burst handling
# --timeout-keep-alive 10: Longer connection reuse for better performance
# --worker-class uvicorn.workers.UvicornWorker: Production-ready worker
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--limit-concurrency", "250", \
     "--backlog", "4096", \
     "--timeout-keep-alive", "10", \
     "--log-level", "info"]