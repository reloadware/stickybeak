FROM python:3.7

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash


# Install common
RUN apt update && apt install net-tools -y && pip3 install pipenv

# Setup motd
COPY docker/motd/motd /etc/motd
COPY docker/motd/.bashrc /root/.bashrc

# uid is set to 1000 for development purposes
RUN useradd -ms /bin/bash -u 1000 django_srv
COPY docker/motd/.bashrc /home/django_srv/.bashrc

RUN chown -R django_srv:django_srv /srv
WORKDIR /srv

# Setup data provider
COPY --chown=django_srv:django_srv flesh .

USER django_srv

# PipEnv
ENV PIPENV_VENV_IN_PROJECT true
RUN pipenv install

EXPOSE 5000

#USER root
