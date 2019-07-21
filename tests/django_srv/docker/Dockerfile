FROM python:3.7-slim-stretch

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash


# Install common
RUN pip3 install pipenv

COPY tests/flask_srv/docker/motd/motd /etc/motd

COPY docker_comm/debug/setup.sh /root/setup_debug.sh
RUN bash /root/setup_debug.sh django_srv
COPY docker_comm/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR /srv

# Setup data provider
COPY tests/django_srv .

# PipEnv
RUN pipenv install --system

COPY stickybeak ./usr/local/lib/python3.7/site-packages/stickybeak

EXPOSE 8000

USER django_srv
