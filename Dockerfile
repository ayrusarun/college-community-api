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

# Performance: Optimized for light-medium load with 2 workers
# --workers 2: Balanced performance + redundancy
# --loop uvloop: Keep high-performance event loop
# --limit-concurrency 150: 300 total concurrent capacity
# --timeout-keep-alive 30: Longer connection reuse
# --no-access-log: Reduce I/O overhead
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--limit-concurrency", "150", \
     "--timeout-keep-alive", "30", \
     "--no-access-log", \
     "--log-level", "error"]