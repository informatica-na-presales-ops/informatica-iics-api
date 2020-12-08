FROM python:3.9.1-alpine3.12

RUN /sbin/apk add --no-cache libpq

COPY requirements.txt /informatica-iics-api/requirements.txt
RUN /usr/local/bin/pip install --no-cache-dir --requirement /informatica-iics-api/requirements.txt

ENV PYTHONUNBUFFERED="1" \
    TZ="Etc/UTC"

ENTRYPOINT ["/usr/local/bin/python"]

COPY get-iics-sessions.py /informatica-iics-api/get-iics-sessions.py
