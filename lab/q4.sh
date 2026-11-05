cd "$(dirname "$0")/.."
. lab/rec.sh evidence/logs/q4-elk.log
C="docker compose -f observability/compose.yml"
A=http://localhost
rec "cat observability/logstash/pipeline.conf"
rec "$C up -d elasticsearch logstash kibana 2>&1 | grep -E 'Started|Running|Healthy'"
rec "until curl -sf $A:9290/_cluster/health >/dev/null; do sleep 3; done; curl -s $A:9290/_cluster/health | jq -c '{cluster_name,status,number_of_nodes}'"
rec "$C ps --format '{{.Service}}  {{.Status}}'"
bash lab/traffic.sh $A:8300 45
sleep 20
rec "$C exec -T app tail -3 /var/log/text-stats/app.log"
rec "curl -s $A:9290/_cat/indices/text-stats-logs?v"
rec "curl -s '$A:9290/text-stats-logs/_search?size=1&sort=@timestamp:desc' | jq '.hits.hits[0]._source | {\"@timestamp\",level,logger,method,route,status,duration_ms}'"
rec "curl -s '$A:9290/text-stats-logs/_count?q=tags:_grokparsefailure' | jq -c '{parse_failures:.count}'"
rec "curl -s $A:9290/text-stats-logs/_search -H 'Content-Type: application/json' -d '{\"size\":0,\"aggs\":{\"levels\":{\"terms\":{\"field\":\"level.keyword\"}},\"routes\":{\"terms\":{\"field\":\"route.keyword\"}}}}' | jq -c '.aggregations | {levels:[.levels.buckets[]|{(.key):.doc_count}],routes:[.routes.buckets[]|{(.key):.doc_count}]}'"
rec "until curl -s $A:5690/api/status | jq -e '.status.overall.level==\"available\"' >/dev/null; do sleep 5; done; curl -s $A:5690/api/status | jq -c '{status:.status.overall.level}'"
rec "curl -s -X POST $A:5690/api/data_views/data_view -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -d '{\"data_view\":{\"id\":\"text-stats\",\"title\":\"text-stats-logs\",\"name\":\"Text Stats Logs\",\"timeFieldName\":\"@timestamp\"}}' | jq -c '.data_view | {id,title,timeFieldName}'"
