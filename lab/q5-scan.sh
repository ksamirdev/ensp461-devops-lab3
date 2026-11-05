cd "$(dirname "$0")/.."
. lab/rec.sh evidence/logs/q5-local-scans.log
T=~/lab-tools/bin
rec "$T/pip-audit -r requirements-dev.txt"
rec "$T/bandit -r service -q"
rec "trivy fs --scanners secret,misconfig --severity HIGH,CRITICAL --ignorefile .trivyignore.yaml --exit-code 1 --skip-dirs .venv . 2>&1 | grep -v INFO"
rec "docker build -q -t text-stats:scan ."
rec "trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 text-stats:scan 2>&1 | grep -v INFO"
