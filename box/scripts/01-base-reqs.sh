#!/bin/bash

export DEBIAN_FRONTEND=noninteractive
echo "===> Making sure system is up to date"
sudo apt-get install apt-transport-https ca-certificates
sudo apt-key update
sudo apt-get -y update
sudo apt-get -y upgrade

#Guest additions requirements
echo "====> Guest additions build reqs"
sudo apt-get install -y gcc build-essential linux-headers-server

#Guest additions
echo "====> Installing virtualbox guest additions"
sudo sudo mount /dev/cdrom /mnt
cd /mnt
sudo sudo ./VBoxLinuxAdditions.run
cd /
sudo umount /mnt

#Install nfs for shared folders
echo "===> Installing NFS subsystem"
sudo apt-get install -y nfs-kernel-server

#Configure eth1 interface (not there by default
echo "====> Adding configuration for eth1"
echo "auto eth1" | sudo tee --append /etc/network/interfaces > /dev/null
echo "iface eth1 inet dhcp" | sudo tee --append /etc/network/interfaces > /dev/null

#Configure SSH
echo "====> Configuring SSH server for port forwarding"
echo "PermitOpen any" | sudo tee --append /etc/ssh/sshd_config > /dev/null
echo "AllowTcpForwarding yes" | sudo tee --append /etc/ssh/sshd_config > /dev/null
sudo service ssh restart
