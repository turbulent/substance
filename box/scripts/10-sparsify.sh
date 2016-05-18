#!/bin/bash -x

export DEBIAN_FRONTEND=noninteractive

echo "Performing image cleanup..."

echo "APT cleanup..."

sudo aptitude -y purge ri
sudo aptitude -y purge installation-report landscape-common wireless-tools wpasupplicant ubuntu-serverguide landscape-client

# Remove APT cache
sudo apt-get clean -y
sudo apt-get autoclean -y

echo "Clear history..."

# Remove bash history
unset HISTFILE
sudo rm -f /root/.bash_history
sudo rm -f /home/substance/.bash_history
history -c

echo "Empty log files..."

# Cleanup log files
sudo find /var/log -type f | while read f; do echo -ne '' | sudo tee $f; done;

echo "Zeroing drive space for /"

# Whiteout root
count=`df --sync -kP / | tail -n1  | awk -F ' ' '{print $4}'`; 
let count--
sudo dd if=/dev/zero of=/tmp/whitespace bs=1024 count=$count;
sudo rm /tmp/whitespace;

echo "Zeroing swap..."
swappart=$(cat /proc/swaps | grep -v Filename | tail -n1 | awk -F ' ' '{print $1}')
if [ "$swappart" != "" ]; then
  sudo swapoff $swappart;
  sudo dd if=/dev/zero of=$swappart;
  sudo mkswap $swappart;
  sudo swapon $swappart;
fi
 
echo "All done."
