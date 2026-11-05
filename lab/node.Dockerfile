# Bare Ubuntu 24.04 with systemd: the managed node. Python and nginx are installed by Ansible.
FROM public.ecr.aws/docker/library/ubuntu:24.04
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends systemd systemd-sysv dbus
STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
