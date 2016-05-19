#!/bin/bash -x

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
echo "substance ALL=(ALL) NOPASSWD:ALL" | sudo tee --append /etc/sudoers.d/substance

#Pass auth sock when using sudo
echo ""
echo "===> Allow ssh forwarding with sudo"
echo "Defaults env_keep += SSH_AUTH_SOCK" | sudo tee --append /etc/sudoers > /dev/null
