#!/usr/bin/env bash

addgroup --gid 1000 stickybeak && adduser --disabled-password --disabled-login --gecos "" --uid 1000 --gid 1000 stickybeak
echo "su stickybeak" >> /root/.bashrc

apt-get update && apt-get install -y openssh-server supervisor
mkdir /var/run/sshd
echo 'stickybeak:password' | chpasswd
echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
echo "AllowUsers stickybeak" >> /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

export NOTVISIBLE="in users profile"
echo "export VISIBLE=now" >> /etc/profile

# uncomment aliases and colors
sed -i '/force_color_prompt=yes/s/^/#/g' /home/stickybeak/.bashrc
echo "alias ll='ls -l'" >> /home/stickybeak/.bashrc
echo "alias la='ls -A'" >> /home/stickybeak/.bashrc

echo "echo -e \"`cat /etc/motd`\"" >> /home/stickybeak/.bashrc
