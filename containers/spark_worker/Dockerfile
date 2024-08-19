FROM bitnami/spark:3.5.2
USER root
RUN apt-get update && apt-get install -y wget

WORKDIR /opt/jobs
RUN wget -P /opt/spark/jars/ https://jdbc.postgresql.org/download/postgresql-42.2.20.jar

COPY requirements.txt /opt/jobs/

RUN pip install --no-cache-dir -r /opt/jobs/requirements.txt
