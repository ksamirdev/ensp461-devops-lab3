# Completeness check, appended to the Q4 log after ingestion settled
cd "$(dirname "$0")/.."
. lab/rec.sh evidence/logs/q4-elk.log
rec "docker compose -f observability/compose.yml exec -T app wc -l /var/log/text-stats/app.log; curl -s localhost:9290/text-stats-logs/_count | jq -c '{indexed_docs:.count}'"
rec "curl -s localhost:9290/_cluster/health | jq -c '{status,unassigned_shards}'"
