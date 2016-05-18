#!/bin/bash -x

export DEBIAN_FRONTEND=noninteractive

#Install docker: 1.9.1 and configure TCP
echo "====> Installing docker engine"
echo deb http://get.docker.com/ubuntu docker main  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
sudo apt-get update
sudo apt-get install -y lxc-docker-1.9.1
echo 'DOCKER_OPTS="-H 0.0.0.0:2375"' | sudo tee --append /etc/default/docker > /dev/null
echo 'export DOCKER_HOST="tcp://127.0.0.1:2375"' | sudo tee /etc/profile.d/docker.sh > /dev/null
sudo service docker restart

echo "===> Installing dockwrkr"
sudo pip install git+ssh://git@gitlab.turbulent.ca:6666/turbulent/dockwrkr.git

echo "===> Installing subwatch"
sudo pip install git+ssh://git@gitlab.turbulent.ca:6666/bbeausej/subwatch.git

