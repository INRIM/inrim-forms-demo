FROM tiangolo/uvicorn-gunicorn:python3.8

LABEL maintainer="Alessio Gerace <a.gerace@inrim.it>"

RUN apt-get update && apt-get install -y libldap-dev git
RUN apt-get install -y libsasl2-dev gcc python3-dev g++

COPY requirements.txt /requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt


COPY app /app


