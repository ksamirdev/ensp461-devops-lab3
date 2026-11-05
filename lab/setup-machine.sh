#!/bin/bash
# Provisions the Ubuntu 24.04 lab machine: orb create ubuntu:noble ensp461-lab3
set -euo pipefail
TERRAFORM=1.17.1
TRIVY=0.76.2
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl unzip git rsync jq python3-venv apache2-utils ansible >/dev/null
# Docker CE, not Ubuntu's docker.io: that package has no buildx and Terraform image builds hang without it
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc >/dev/null
echo "deb [signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null
sudo systemctl enable --now docker.socket docker
sudo usermod -aG docker "$USER"
curl -fsSLo /tmp/tf.zip "https://releases.hashicorp.com/terraform/${TERRAFORM}/terraform_${TERRAFORM}_linux_arm64.zip"
sudo unzip -qo /tmp/tf.zip terraform -d /usr/local/bin
curl -fsSL "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY}/trivy_${TRIVY}_Linux-ARM64.tar.gz" | sudo tar xz -C /usr/local/bin trivy
python3 -m venv ~/lab-tools
~/lab-tools/bin/pip install -q pip-audit bandit -r "$(dirname "$0")/../requirements-dev.txt"
