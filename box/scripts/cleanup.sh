#!/bin/bash -e

#Purge unused packages.
aptitude -y purge ri
aptitude -y purge installation-report landscape-common wireless-tools wpasupplicant ubuntu-serverguide landscape-client

# delete all linux headers
dpkg --list | awk '{ print $2 }' | grep linux-headers | xargs apt-get -y purge

# this removes specific linux kernels, such as
# linux-image-3.11.0-15-generic but 
# * keeps the current kernel
# * does not touch the virtual packages, e.g.'linux-image-generic', etc.
#
dpkg --list | awk '{ print $2 }' | grep 'linux-image-3.*-generic' | grep -v `uname -r` | xargs apt-get -y purge

# delete linux source
dpkg --list | awk '{ print $2 }' | grep linux-source | xargs apt-get -y purge

# delete development packages
dpkg --list | awk '{ print $2 }' | grep -- '-dev$' | xargs apt-get -y purge

# delete compilers and other development tools
apt-get -y purge cpp gcc g++ python-dev libffi libffi-dev libssl-dev

# delete X11 libraries
apt-get -y purge libx11-data xauth libxmuu1 libxcb1 libx11-6 libxext6

# delete obsolete networking
apt-get -y purge ppp pppconfig pppoeconf

# delete oddities
apt-get -y purge popularity-contest

apt-get -y autoremove
apt-get -y clean
apt-get -y autoclean

rm -rf /var/lib/apt/lists/*


# Clean up udev
set +e
rm /var/lib/dhcp/*
rm /etc/udev/rules.d/70-persistent-net.rules
mkdir /etc/udev/rules.d/70-persistent-net.rules
rm -rf /dev/.udev/
rm /lib/udev/rules.d/75-persistent-net-generator.rules

# Wipe MAC addy
for nic in /etc/sysconfig/network-scripts/ifcfg-eth*; do sed -i /HWADDR/d $nic; done
set -e

#Clean out the logs & history
find /var/log -type f | while read f; do echo -ne '' | tee $f; done;
rm -f /root/.bash_history
history -c

