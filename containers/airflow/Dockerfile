FROM apache/airflow:slim-latest-python3.11
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         openjdk-17-jre-headless wget procps\
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/spark/jars/
RUN wget -P /opt/spark/jars/ https://jdbc.postgresql.org/download/postgresql-42.2.20.jar

USER airflow

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" apache-airflow-providers-apache-spark==4.9.0
COPY requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt
