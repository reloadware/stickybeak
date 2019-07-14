FROM python:3.7-slim-stretch

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash


# Install common
RUN pip3 install pipenv

# uncomment aliases and colors
RUN sed -i '9,14 s/# *//' /root/.bashrc
RUN sed -i '16,30 s/# *//' /root/.bashrc

# Setup motd
COPY docker/motd/motd /etc/motd
RUN echo "echo -e \"`cat /etc/motd`\"" >> /root/.bashrc

WORKDIR /srv

# Setup data provider
COPY tests/flask_srv .

RUN pipenv install --system

COPY stickybeak /usr/local/lib/python3.7/site-packages/stickybeak

ENV FLASK_APP app.py
ENV FLASK_ENV development
ENV FLASK_DEBUG 1

EXPOSE 5000
