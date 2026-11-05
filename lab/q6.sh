cd "$(dirname "$0")/.."
. lab/rec.sh evidence/logs/q6-testing.log
A=http://localhost
J='Content-Type: application/json'
T=~/lab-tools/bin
rec "$T/python -m pytest -v -p no:cacheprovider 2>&1 | tail -16"
docker rm -f flag-off flag-on selenium >/dev/null 2>&1; docker network create lab3-e2e >/dev/null 2>&1
rec "docker build -q -t text-stats:3.0.0 ."
rec "docker run -d --name flag-off --network lab3-e2e -p 127.0.0.1:8320:5000 -e FEATURE_TOP_WORDS=false text-stats:3.0.0"
rec "docker run -d --name flag-on --network lab3-e2e -p 127.0.0.1:8321:5000 -e FEATURE_TOP_WORDS=true text-stats:3.0.0"
sleep 4
rec "curl -s -w ' HTTP %{http_code}\n' -H '$J' -d '{\"text\":\"a a b\"}' $A:8320/stats/top"
rec "curl -s -w ' HTTP %{http_code}\n' -H '$J' -d '{\"text\":\"a a b\"}' $A:8321/stats/top"
rec "ab -q -n 5000 -c 50 $A:8300/healthz | grep -E 'Concurrency|Complete requests|Failed|Requests per second|Time per request|99%|100%'"
printf '{"text":"load testing the text stats service"}' > /tmp/body.json
rec "ab -q -n 5000 -c 50 -p /tmp/body.json -T application/json $A:8300/stats | grep -E 'Concurrency|Complete requests|Failed|Non-2xx|Requests per second|Time per request|99%|100%'"
rec "ab -q -n 20000 -c 200 $A:8300/healthz | grep -E 'Concurrency|Complete requests|Failed|Non-2xx|Requests per second|99%|100%'"
rec "docker run -d --name selenium --network lab3-e2e --shm-size=1g -p 127.0.0.1:4444:4444 mirror.gcr.io/selenium/standalone-chromium:latest"
rec "until curl -sf $A:4444/status | jq -e .value.ready >/dev/null; do sleep 2; done; curl -s $A:4444/status | jq -c '{ready:.value.ready}'"
rec "$T/python e2e/test_ui_selenium.py http://flag-on:5000 $A:4444 evidence/screenshots"
docker rm -f flag-off selenium >/dev/null
