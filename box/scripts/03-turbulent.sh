#!/bin/bash -x

export DEBIAN_FRONTEND=noninteractive

# Developer DNS / docker registry
echo "Adding Turbulent docker-registry host lookup"
sudo sed -i "2i10.0.20.35 docker-registry" /etc/hosts

#ssh known hosts for Turbulent & Github
sudo mkdir -p /root/.ssh && sudo touch /root/.ssh/known_hosts
echo "Performing keyscan for gitlab.turbulent.ca and github.com"
ssh-keyscan -H -p6666 gitlab.turbulent.ca | sudo tee --append /root/.ssh/known_hosts > /dev/null
ssh-keyscan -H github.com | sudo tee --append /root/.ssh/known_hosts > /dev/null
sudo cp /root/.ssh/known_hosts ~substance/.ssh/known_hosts
echo -e "Host gitlab.turbulent.ca\n\tUser git\n\tPort 6666\n\tStrictHostKeyChecking no\n" >> ~substance/.ssh/config
sudo chown -R substance:substance ~substance/.ssh
sudo chmod -R 700 ~substance/.ssh

#Git
echo "Installing git-core"
sudo apt-get install -y git-core

#git config
echo "Configure push simple on git-core"
git config --global push.default simple
