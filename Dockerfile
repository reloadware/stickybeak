FROM python:3.7-slim-stretch

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash


# Install common
RUN pip3 install pipenv

WORKDIR /srv

COPY . .
RUN pipenv install -d --system

COPY docker/motd/motd /etc/motd

COPY docker/sshd/setup.sh /root/setup_sshd.sh
RUN bash /root/setup_sshd.sh

COPY docker/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

USER stickybeak
