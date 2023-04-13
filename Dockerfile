FROM python:3
USER root

WORKDIR /app

COPY ./ta-lib-0.4.0-src.tar.gz .
COPY ./requirements .

RUN apt-get update

RUN tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/usr --build=aarch64-unknown-linux-gnu && \
  make && \
  make install

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
