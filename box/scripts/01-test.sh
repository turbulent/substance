#!/bin/bash -x

ssh-add -l
ssh git@gitlab.turbulent.ca

sudo ssh-add -l
sudo git@gitlab.turbulent.ca
