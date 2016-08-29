
sysctl-perf:
  file.blockreplace:
    - name: /etc/sysctl.conf
    - marker_start: "# BLOCK SALT : salt managed PERFORMANCE"
    - marker_end: "# BLOCK SALT : PERFORMANCE"
    - content: |
        vm.swappiness=10
        net.core.rmem_max=8388608
        net.core.wmem_max=8388608
        net.core.rmem_default=65536
        net.core.wmem_default=65536
        net.ipv4.tcp_rmem=8192 873800 8388608
        net.ipv4.tcp_wmem=4096 655360 8388608
        net.ipv4.tcp_mem=8388608 8388608 8388608
        net.ipv4.tcp_max_tw_buckets=6000000
        net.ipv4.tcp_max_syn_backlog=65536
        net.ipv4.tcp_max_orphans=262144
        net.core.somaxconn = 16384
        net.core.netdev_max_backlog = 16384
        net.ipv4.tcp_synack_retries = 2
        net.ipv4.tcp_syn_retries = 2
        net.ipv4.tcp_fin_timeout = 7
        net.ipv4.tcp_slow_start_after_idle = 0
        net.ipv4.tcp_keepalive_time=60
        net.ipv4.tcp_keepalive_intvl=60
        net.ipv4.tcp_keepalive_probes=5
        net.ipv4.tcp_congestion_control = cubic
        net.ipv4.tcp_syncookies = 1
        fs.inotify.max_user_watches=524288
        fs.inotify.max_user_instances=1024
    - show_changes: True
    - append_if_not_found: True
sysctl-perf-reload:
  cmd.run:
    - name: /sbin/sysctl -p
