FROM mirror.gcr.io/library/python:3.13-slim
WORKDIR /srv/text-stats
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY service service
RUN useradd --system textstats && mkdir /var/log/text-stats && chown textstats /var/log/text-stats
USER textstats
ENV RELEASE=3.0.0
EXPOSE 5000
HEALTHCHECK --interval=10s --timeout=3s CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://localhost:5000/healthz', timeout=2)"]
# ponytail: one worker because prometheus_client counters are per process; multiprocess mode if more are needed
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", "service.web:app"]
