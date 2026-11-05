cd "$(dirname "$0")/.."
. lab/rec.sh evidence/logs/q3-monitoring.log
A=http://localhost
rec "cat observability/prometheus.yml"
rec "docker compose -f observability/compose.yml up -d --build app prometheus grafana 2>&1 | grep -E 'Started|Running|Healthy|Built'"
sleep 15
rec "docker compose -f observability/compose.yml ps --format '{{.Service}}  {{.Image}}  {{.Status}}  {{.Ports}}'"
rec "curl -s $A:8300/healthz"
bash lab/traffic.sh $A:8300 60
rec "curl -s $A:8300/metrics | grep -E '^textstats_(http_requests_total|words_processed_total)'"
rec "curl -s $A:9390/api/v1/targets | jq -r '.data.activeTargets[] | \"\\(.labels.job) \\(.scrapeUrl) \\(.health)\"'"
rec "curl -s --get $A:9390/api/v1/query --data-urlencode 'query=sum by (route) (rate(textstats_http_requests_total[1m]))' | jq -r '.data.result[] | \"\\(.metric.route) \\(.value[1]) req/s\"'"
rec "curl -s $A:3390/api/health | jq -c '{database,version}'"
rec "curl -s $A:3390/api/dashboards/uid/text-stats | jq -r '.dashboard.title, (.dashboard.panels[].title)'"
