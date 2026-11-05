# ENSP461 Lab 3 - Monitoring, Logging and DevSecOps

Author: Samir Kumar Gupta (Roll No. 2301730243)

The text statistics service from Lab 1, now configured with Ansible, provisioned with Terraform, monitored with Prometheus and Grafana, logged with the ELK stack, and gated by a DevSecOps pipeline in Jenkins.
Feature flags, load testing and Selenium browser tests complete the workflow.

## Reports

One PDF per question in [`reports/`](reports/):

| Question | Report |
|---|---|
| Q1 Ansible configuration management | [q1-ansible-configuration.pdf](reports/q1-ansible-configuration.pdf) |
| Q2 Terraform infrastructure as code | [q2-terraform-iac.pdf](reports/q2-terraform-iac.pdf) |
| Q3 Prometheus and Grafana monitoring | [q3-prometheus-grafana.pdf](reports/q3-prometheus-grafana.pdf) |
| Q4 Centralized logging with ELK | [q4-elk-centralized-logging.pdf](reports/q4-elk-centralized-logging.pdf) |
| Q5 DevSecOps pipeline | [q5-devsecops-pipeline.pdf](reports/q5-devsecops-pipeline.pdf) |
| Q6 Feature flags, load testing, Selenium | [q6-feature-flags-testing.pdf](reports/q6-feature-flags-testing.pdf) |
| Q7 Monitoring, logging and DevSecOps report | [q7-monitoring-devsecops-report.pdf](reports/q7-monitoring-devsecops-report.pdf) |

Every command output in the reports is copied from the logs in [`evidence/logs/`](evidence/logs/), which `lab/rec.sh` recorded while the commands ran.
Screenshots are in [`evidence/screenshots/`](evidence/screenshots/).
`python3 lab/build_reports.py` rebuilds the PDFs from that evidence.

## Layout

- `service/` - Flask app: `/stats`, `/stats/top` (feature flag), `/ui`, `/metrics`, structured request logs
- `tests/` - pytest unit tests
- `e2e/` - Selenium browser test
- `automation/` - Ansible inventory, playbook and templates (Q1)
- `infra/` - Terraform config for scalable containers (Q2)
- `observability/` - Prometheus, Grafana provisioning, Logstash pipeline, compose file (Q3, Q4)
- `pipeline/` - Jenkinsfile, Jenkins image and job definition (Q5)
- `lab/` - lab machine setup, one recorded script per question, report builder
- `evidence/` - command logs, Jenkins console logs, screenshots

## Environment

Everything ran on an OrbStack Ubuntu 24.04 machine (arm64) on macOS:

```
orb create ubuntu:noble ensp461-lab3
lab/sync.sh to                     # copy the repo into the machine
orb -m ensp461-lab3 bash ~/ensp461-lab3/lab/setup-machine.sh
```

The setup installs Docker CE, Ansible, Terraform 1.17.1, Trivy 0.76.2, ApacheBench, pip-audit and bandit.
macOS keeps `~/Desktop` private from OrbStack, so `lab/sync.sh` copies the project into the machine, and `lab/sync.sh back` copies the evidence out.

## Running each part

Run these inside the machine from `~/ensp461-lab3`.

```
bash lab/nodes.sh && bash lab/q1.sh     # Q1: two systemd nodes, playbook twice
bash lab/q2.sh                          # Q2: terraform init/plan/apply, scale 2 -> 4 -> 2
bash lab/q3.sh                          # Q3: app + Prometheus (:9390) + Grafana (:3390)
bash lab/q4.sh                          # Q4: Elasticsearch (:9290) + Logstash + Kibana (:5690)
docker compose -f pipeline/compose.yml up -d --build   # Q5: Jenkins on :8390
bash lab/q5-scan.sh                     # Q5: same scans as the pipeline, locally
bash lab/q6.sh                          # Q6: flag on/off, ApacheBench, Selenium
```

All ports bind to 127.0.0.1.
Grafana allows anonymous read-only access, and Elasticsearch and Jenkins have security turned off.
Both are acceptable only on this local lab machine.

## Pipeline

The Jenkins job `text-stats-devsecops` polls this repository every 2 minutes and runs:

unit tests -> pip-audit -> bandit -> trivy fs (secrets, misconfig) -> docker build -> trivy image

Any finding fails its stage and blocks the build.
Builds 2, 3 and 4 were each blocked by a different gate on real findings, and each fix is its own commit; build 5 passed.
The details are in the Q5 report.
