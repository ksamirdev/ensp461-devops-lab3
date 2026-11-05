cd "$(dirname "$0")/.."
. lab/rec.sh evidence/logs/q7-environment.log
rec "cat /etc/os-release | head -1; uname -srm"
rec "docker version --format 'Docker Engine {{.Server.Version}}'; docker compose version"
rec "ansible --version | head -1; terraform version | head -1; trivy --version | head -1"
rec "~/lab-tools/bin/pip-audit --version; ~/lab-tools/bin/bandit --version | head -1; ab -V | head -1"
rec "docker exec lab3-pipeline-jenkins-1 cat /var/jenkins_home/war/META-INF/MANIFEST.MF | grep Jenkins-Version"
rec "docker images --format '{{.Repository}}:{{.Tag}}' | grep -E 'prometheus|grafana|elastic|selenium|jenkins' | sort"
