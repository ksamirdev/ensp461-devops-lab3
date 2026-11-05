# Real traffic through the app: normal calls plus deliberate bad requests. usage: traffic.sh <base-url> <seconds>
end=$((SECONDS + $2))
while [ $SECONDS -lt $end ]; do
  curl -s -o /dev/null "$1/"; curl -s -o /dev/null "$1/healthz"; curl -s -o /dev/null "$1/ui"
  curl -s -o /dev/null -H 'Content-Type: application/json' -d '{"text":"monitoring the text stats service with real requests"}' "$1/stats"
  curl -s -o /dev/null -H 'Content-Type: application/json' -d '{"text":42}' "$1/stats"
  curl -s -o /dev/null "$1/missing"
  sleep 0.3
done
