# Ubuntu 24.04 control machine: every lab command runs here against the shared Docker engine
FROM public.ecr.aws/docker/library/ubuntu:24.04
ARG TERRAFORM=1.17.1
ARG TRIVY=0.76.2
RUN apt-get update -qq \
 && apt-get install -y -qq ca-certificates curl unzip git python3-venv apache2-utils ansible docker.io docker-compose-v2 jq >/dev/null \
 && curl -fsSLo /tmp/tf.zip https://releases.hashicorp.com/terraform/${TERRAFORM}/terraform_${TERRAFORM}_linux_arm64.zip \
 && unzip -q /tmp/tf.zip terraform -d /usr/local/bin \
 && curl -fsSL https://github.com/aquasecurity/trivy/releases/download/v${TRIVY}/trivy_${TRIVY}_Linux-ARM64.tar.gz | tar xz -C /usr/local/bin trivy \
 && useradd -m -s /bin/bash -G root samir
CMD ["sleep", "infinity"]
