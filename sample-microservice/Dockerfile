FROM ubuntu:16.04

RUN apt-get update 
RUN apt-get install -y build-essential python-pip python-dev
RUN pip install --upgrade pip

RUN mkdir -p /opt/microservices
ADD . /opt/microservices
RUN pip install -r /opt/microservices/requirements.txt

WORKDIR /opt/microservices
EXPOSE 5000

CMD python server.py
