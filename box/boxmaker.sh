#!/bin/bash -x

VBOX_ADD_ISO="/Applications/VirtualBox.app/Contents/MacOS/VBoxGuestAdditions.iso"
BOX_OVF="substance-min.ovf"
BOX_PORT="6666"
KEY="../support/substance_insecure"
VMNAME="substance"

VBoxManage import --vsys 0 --vmname ${VMNAME} --cpus 1 --memory 512 ${BOX_OVF}
VBoxManage storageattach ${VMNAME} --storagectl "IDE" --port 0 --device 0 --type dvddrive --medium ${VBOX_ADD_ISO}
VBoxManage modifyvm ${VMNAME} --nic1 nat --natnet1 default
VBoxManage modifyvm ${VMNAME} --nic2 hostonly 
VBoxManage modifyvm ${VMNAME} --natpf1 "substance-ssh",tcp,,${BOX_PORT},,22
VBoxManage modifyvm ${VMNAME} --usb off --audio none
VBoxManage startvm --type headless ${VMNAME}

echo "===> Waiting for box to boot"
sleep 10

ssh -t substance@127.0.0.1 -p6666 <<'END'
#Install the substance ssh key
echo ""
echo "====> Installing substance SSH keys"
mkdir -p /home/substance/.ssh
chmod 0700 /home/substance/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9KutC+/Zwowb/Tnw+xbjGCKmTlSzTcM4i1BI3MCIZuA5pajVNz4/Uxmx3DkATGdsi82WhGg0HknG5AS+9s6P6z9dhlPCjghbL8LlM253KqVGjEEI0cE8GkpvJS8IY8iqYICCE1ib73qxx/3ASL06r5Z0TIeg7draClTNrIf6xn85Ty/GJ1SMrmJ72N/R3+6YDIN9LLGi2Ze/05mQb6kn8Ue4Iu/kAcjqCBZYZKfKaiMsGH9AL2YDziccTtAn0vnTbK8FeXsadX+QybhagYLopjs7x8zGCZB8qGMCD40OX6vTTPq+X5hjrvAgjogR4uZDIZvyNZTMMFm/B1V3LEKLP substance_insecure" > /home/substance/.ssh/authorized_keys
chmod 0600 /home/substance/.ssh/authorized_keys
chown -R substance /home/substance/.ssh

#Allow substance to sudo
echo ""
echo "===> Allow substance to sudo"
echo "substance" | sudo -S bash -c 'echo "substance ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/substance'

#Pass auth sock when using sudo
echo ""
echo "===> Allow ssh forwarding with sudo"
echo "substance" | sudo -S bash -c 'echo "Defaults env_keep += SSH_AUTH_SOCK" >> /etc/sudoers'
echo "substance" | sudo -S bash -c 'echo 'chmod -R 777 `dirname $SSH_AUTH_SOCK`' >> /home/substance/.profile'
END

cat scripts/01-base-reqs.sh | ssh -t substance@127.0.0.1 -i ${KEY} -p${BOX_PORT} 
cat scripts/02-tools.sh | ssh -t substance@127.0.0.1 -i ${KEY} -p${BOX_PORT} 
cat scripts/03-turbulent.sh | ssh -t substance@127.0.0.1 -i ${KEY} -p${BOX_PORT} 
cat scripts/10-sparsify.sh | ssh -t substance@127.0.0.1 -i ${KEY} -p${BOX_PORT} 


VBoxManage controlvm ${VMNAME} poweroff soft
echo "=====> Waiting for machine to shut down..."
sleep 10 
echo "=====> Exporting VM"
rm -f box.ovf box-disk1.vmdk
VBoxManage export ${VMNAME} -o box.ovf
echo "=====> Compressing package"

tar -zcvf substance-box-0.1.box box.yml box.ovf box-disk1.vmdk

VBoxManage unregistervm --delete ${VMNAME}
