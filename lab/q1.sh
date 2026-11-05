cd /Users/samir/lab3-run
. lab/rec.sh evidence/logs/q1-ansible.log
rec "ansible --version | head -1"
rec "docker ps --filter name=web-node --format '{{.Names}}  {{.Image}}  {{.Status}}  {{.Ports}}'"
rec "cat automation/inventory.ini"
rec "ansible -i automation/inventory.ini webnodes -m raw -a 'cat /etc/os-release | head -1'"
rec "ANSIBLE_DEPRECATION_WARNINGS=false ANSIBLE_FORCE_COLOR=0 ansible-playbook -i automation/inventory.ini automation/site.yml"
rec "ANSIBLE_FORCE_COLOR=0 ansible-playbook -i automation/inventory.ini automation/site.yml | tail -4"
rec "ansible -i automation/inventory.ini webnodes -m command -a 'systemctl is-active text-stats nginx'"
rec "curl -s http://host.docker.internal:8301/healthz"
rec "curl -s http://host.docker.internal:8302/stats -H 'Content-Type: application/json' -d '{\"text\": \"configured by ansible configured twice\"}'"
