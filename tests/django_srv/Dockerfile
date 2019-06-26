FROM python:3.7

ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV SHELL /bin/bash


# Install common
RUN apt update && apt install net-tools -y && pip3 install pipenv
#RUN mkdir /var/run/sshd
#RUN echo 'root:password' | chpasswd
#RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
#RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
#ENV NOTVISIBLE "in users profile"
#RUN echo "export VISIBLE=now" >> /etc/profile
#EXPOSE 22
#CMD ["/usr/sbin/sshd"]

# Setup motd
COPY docker/motd/motd /etc/motd
COPY docker/motd/.bashrc /root/.bashrc

# uid is set to 1000 for development purposes
RUN useradd -ms /bin/bash -u 1000 django_srv
COPY docker/motd/.bashrc /home/django_srv/.bashrc

RUN chown -R django_srv:django_srv /srv
WORKDIR /srv

# supervisord
#COPY docker/supervisor/supervisor.conf /etc/supervisor.conf

# Setup data provider
COPY --chown=django_srv:django_srv flesh .

USER django_srv

# PipEnv
ENV PIPENV_VENV_IN_PROJECT true
RUN pipenv install

EXPOSE 5000

#USER root
