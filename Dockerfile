FROM dockerhub.paypalcorp.com/python:3.11-slim

WORKDIR /app

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

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]