# Jenkins controller with the scanners the pipeline calls. Docker runs through the host socket.
FROM mirror.gcr.io/jenkins/jenkins:lts-jdk21
ARG TRIVY=0.76.2
USER root
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends python3-venv docker.io >/dev/null \
 && curl -fsSL "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY}/trivy_${TRIVY}_Linux-ARM64.tar.gz" | tar xz -C /usr/local/bin trivy
RUN jenkins-plugin-cli --plugins workflow-aggregator git junit
ENV JAVA_OPTS=-Djenkins.install.runSetupWizard=false
