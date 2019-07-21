FROM python:3.7-slim-stretch

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash


RUN pip3 install pipenv

WORKDIR /srv

COPY . .
RUN pipenv install -d --system

COPY docker/motd/motd /etc/motd

COPY docker_comm/debug/setup.sh /root/setup_debug.sh
RUN bash /root/setup_debug.sh stickybeak

COPY docker_comm/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
