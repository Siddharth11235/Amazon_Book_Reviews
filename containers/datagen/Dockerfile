FROM python:3.11.9-slim-bookworm

WORKDIR /opt/datagen

COPY requirements.txt /opt/datagen/

RUN pip install --no-cache-dir -r /opt/datagen/requirements.txt

# Exposing Ports
EXPOSE 5000

# Env python options
ENV PYTHONUNBUFFERED=1
