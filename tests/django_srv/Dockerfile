FROM python:3.7

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash


# Install common
RUN apt update && apt install net-tools -y && pip3 install pipenv

# Setup motd
COPY tests/django_srv/docker/motd/motd /etc/motd
COPY tests/django_srv/docker/motd/.bashrc /root/.bashrc

# uid is set to 1000 for development purposes
RUN useradd -ms /bin/bash -u 1000 django_srv
COPY tests/django_srv/docker/motd/.bashrc /home/django_srv/.bashrc

RUN chown -R django_srv:django_srv /srv
WORKDIR /srv

# Setup data provider
COPY --chown=django_srv:django_srv tests/django_srv/flesh .

USER django_srv

# PipEnv
ENV PIPENV_VENV_IN_PROJECT true
RUN pipenv install

COPY --chown=django_srv:django_srv stickybeak .venv/lib/python3.7/site-packages/stickybeak

EXPOSE 8000
