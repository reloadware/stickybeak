FROM python:3.7

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash


# Install common
RUN apt update && apt install net-tools -y && pip3 install pipenv

# Setup motd
COPY tests/flask_srv/docker/motd/motd /etc/motd
COPY tests/flask_srv/docker/motd/.bashrc /root/.bashrc

# uid is set to 1000 for development purposes
RUN useradd -ms /bin/bash -u 1000 flask_srv
COPY tests/flask_srv/docker/motd/.bashrc /home/flask_srv/.bashrc

RUN chown -R flask_srv:flask_srv /srv
WORKDIR /srv

# Setup data provider
COPY --chown=flask_srv:flask_srv tests/flask_srv/flesh .

USER flask_srv

# PipEnv
ENV PIPENV_VENV_IN_PROJECT true
RUN pipenv install

COPY --chown=flask_srv:flask_srv stickybeak .venv/lib/python3.7/site-packages/stickybeak

ENV FLASK_APP app.py
ENV FLASK_ENV development
ENV FLASK_DEBUG 1

EXPOSE 5000
