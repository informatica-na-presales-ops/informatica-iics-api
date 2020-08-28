FROM python:3.8.5-alpine3.12

COPY requirements.txt /informatica-iics-api/requirements.txt
RUN /usr/local/bin/pip install --no-cache-dir --requirement /informatica-iics-api/requirements.txt
