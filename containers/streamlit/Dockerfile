FROM python:3.11.9-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

RUN python3 -m textblob.download_corpora


EXPOSE 8501

ENTRYPOINT ["bash", "/streamlit/run.sh"]
