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

# Performance: Optimized for burst loads (300-400 req in 2-3s)
# --workers 2: One per vCPU
# --limit-concurrency 200: Max 200 concurrent requests per worker
# --backlog 2048: Queue up to 2048 requests during burst
# --timeout-keep-alive 5: Reuse connections for 5s
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--limit-concurrency", "200", \
     "--backlog", "2048", \
     "--timeout-keep-alive", "5", \
     "--log-level", "info"]