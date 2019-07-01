FROM python:3.7

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash


# Install common
RUN apt update && apt install rsync -y && pip3 install pipenv

# Setup motd
COPY docker/motd/motd /etc/motd
COPY docker/motd/.bashrc /root/.bashrc

# uid is set to 1000 for development purposes
RUN useradd -ms /bin/bash -u 1000 stickybeak
COPY docker/motd/.bashrc /home/stickybeak/.bashrc

RUN chown -R stickybeak:stickybeak /srv
WORKDIR /srv

COPY --chown=stickybeak:stickybeak . .
USER stickybeak

# PipEnv
ENV PIPENV_VENV_IN_PROJECT true
RUN pipenv install -d
