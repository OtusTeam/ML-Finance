FROM python:3.12

RUN set -ex\
    && apt update \
    && apt --yes install libpq-dev \
    && apt --yes install gcc g++ make \
    && pip install mlflow boto3 psycopg2 --no-cache-dir \
    && apt --yes purge gcc g++ make \
    && apt --yes autoremove \
    && apt --yes clean