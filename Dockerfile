FROM python:3.6-alpine
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
COPY requirements.txt /app/
WORKDIR /app

RUN pip install -r requirements.txt
COPY flower_prometheus_exporter.py monitors.py docker-entrypoint.sh /app/
ENTRYPOINT ["/bin/sh", "/app/docker-entrypoint.sh"]
CMD []

EXPOSE 8888
