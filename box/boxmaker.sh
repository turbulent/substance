#!/bin/bash -x

VBOX_ADD_ISO="/Applications/VirtualBox.app/Contents/MacOS/VBoxGuestAdditions.iso"
BOX_OVF="minimal.ova"
BOX_PORT="6666"
KEY="../support/substance_insecure"
VMNAME="substance"
SSHOPTS="-X -A -t -o StrictHostKeyChecking=no"

VBoxManage import --vsys 0 --vmname ${VMNAME} --cpus 1 --memory 1024 ${BOX_OVF}
VBoxManage storageattach ${VMNAME} --storagectl "IDE" --port 0 --device 0 --type dvddrive --medium ${VBOX_ADD_ISO}
VBoxManage modifyvm ${VMNAME} --nic1 nat --natnet1 default
VBoxManage modifyvm ${VMNAME} --natpf1 "substance-ssh",tcp,,${BOX_PORT},,22
VBoxManage modifyvm ${VMNAME} --usb off --audio none
VBoxManage startvm --type headless ${VMNAME}

echo "===> Waiting for box to boot"
sleep 10

ssh -t substance@127.0.0.1 -o StrictHostKeyChecking=no -p${BOX_PORT} <<'END'
echo ""
echo "====> Installing substance_insecure SSH key"
sudo mkdir -p /root/.ssh
sudo chmod 0700 /root/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9KutC+/Zwowb/Tnw+xbjGCKmTlSzTcM4i1BI3MCIZuA5pajVNz4/Uxmx3DkATGdsi82WhGg0HknG5AS+9s6P6z9dhlPCjghbL8LlM253KqVGjEEI0cE8GkpvJS8IY8iqYICCE1ib73qxx/3ASL06r5Z0TIeg7draClTNrIf6xn85Ty/GJ1SMrmJ72N/R3+6YDIN9LLGi2Ze/05mQb6kn8Ue4Iu/kAcjqCBZYZKfKaiMsGH9AL2YDziccTtAn0vnTbK8FeXsadX+QybhagYLopjs7x8zGCZB8qGMCD40OX6vTTPq+X5hjrvAgjogR4uZDIZvyNZTMMFm/B1V3LEKLP substance_insecure"  | sudo tee --append /root/.ssh/authorized_keys > /dev/null
sudo chmod 0600 /root/.ssh/authorized_keys
wget -O - https://repo.saltstack.com/apt/ubuntu/14.04/amd64/2016.3/SALTSTACK-GPG-KEY.pub | sudo apt-key add -
echo "deb http://repo.saltstack.com/apt/ubuntu/14.04/amd64/2016.3 trusty main" | sudo tee --append /etc/apt/sources.list.d/saltstack.list > /dev/null
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y salt-minion rsync
END

#Copy our salt states
rsync -ave "ssh ${SSHOPTS} -p ${BOX_PORT} -i ${KEY}" salt/* root@127.0.0.1:/srv/

#Run salt configurator
ssh ${SSHOPTS} -i ${KEY} -p ${BOX_PORT} root@127.0.0.1 'salt-call --local state.sls substance.box.minion'
ssh ${SSHOPTS} -i ${KEY} -p ${BOX_PORT} root@127.0.0.1 'salt-call --local state.highstate'

VBoxManage controlvm ${VMNAME} poweroff soft
echo "=====> Waiting for machine to shut down..."
sleep 10 

echo "=====> Exporting VM"
rm -f box.ovf box-disk1.vmdk
VBoxManage export ${VMNAME} -o box.ovf
echo "=====> Compressing package"
tar -zcvf substance-box-0.1.box box.yml box.ovf box-disk1.vmdk

VBoxManage unregistervm --delete ${VMNAME}
