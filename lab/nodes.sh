# Starts the two systemd web nodes that Ansible configures (host ports 8301, 8302)
docker build -q -t ensp461-lab3-node -f lab/node.Dockerfile lab
for i in 1 2; do
  docker run -d --privileged --cgroupns=host --name web-node-$i --hostname web-node-$i \
    -v /sys/fs/cgroup:/sys/fs/cgroup -p 127.0.0.1:830$i:80 ensp461-lab3-node
done
