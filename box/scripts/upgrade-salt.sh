#!/bin/bash

wget -O - https://repo.saltstack.com/apt/ubuntu/14.04/amd64/2016.3/SALTSTACK-GPG-KEY.pub | apt-key add -
echo 'deb http://repo.saltstack.com/apt/ubuntu/14.04/amd64/2016.3 trusty main' | tee --append /etc/apt/sources.list.d/saltstack.list > /dev/null
apt-get update -y 
apt-get upgrade -y
apt-get install -y salt-minion rsync
