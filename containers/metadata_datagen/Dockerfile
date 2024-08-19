FROM bitnami/spark:3.5.2
USER root
RUN apt-get update && apt-get install -y wget

WORKDIR /opt/datagen
RUN wget -P /opt/spark/jars/ https://jdbc.postgresql.org/download/postgresql-42.2.20.jar

COPY requirements.txt /opt/datagen/

RUN pip install --no-cache-dir -r /opt/datagen/requirements.txt

ENTRYPOINT ["python3", "/opt/datagen/metadata_db.py"]
