
substance-purge-aptitude:
  cmd.run:
    - names: 
      - aptitude -y purge ri
      - aptitude -y purge installation-report landscape-common wireless-tools wpasupplicant ubuntu-serverguide landscape-client

substance-purge-apt:
  cmd.run:
    - names:
      - apt-get clean -y
      - apt-get autoclean -y

substance-purge-history:
  cmd.run:
    - names:
      - rm -f /root/.bash_history 
      - rm -f /substance/.bash_history
      - history -c

substance-purge-logs:
  cmd.run:
    - name: find /var/log -type f | while read f; do echo -ne '' | sudo tee $f; done;

substance-zero-drive:
  cmd.run:
    - name: |
        count=`df --sync -kP / | tail -n1  | awk -F ' ' '{print $4}'`;
        let count--
        dd if=/dev/zero of=/tmp/whitespace bs=1024 count=$count;
        rm /tmp/whitespace;

substance-zero-swap:
  cmd.run:
    - name: |
        swappart=$(cat /proc/swaps | grep -v Filename | tail -n1 | awk -F ' ' '{print $1}')
        if [ "$swappart" != "" ]; then
          sudo swapoff $swappart;
          sudo dd if=/dev/zero of=$swappart;
          sudo mkswap $swappart;
          sudo swapon $swappart;
        fi
