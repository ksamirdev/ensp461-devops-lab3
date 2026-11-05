"""Per-question report content. Every number quoted here comes from evidence/logs."""
from build_reports import bullets, config, shot, term


def q1():
    log = "q1-ansible.log"
    return "".join([
        "<h2>Setup</h2>",
        "<p>Two managed nodes are bare Ubuntu 24.04 containers running systemd (<code>lab/node.Dockerfile</code>). "
        "They start with no Python, nginx or application. Ansible reaches them through the "
        "<code>community.docker.docker</code> connection plugin, so no SSH keys are needed.</p>",
        term(log, "docker ps", "cat automation/inventory", "os-release"),
        "<h2>Playbook</h2>",
        config("automation/site.yml"),
        "<p>The app runs under systemd as an unprivileged <code>textstats</code> user, bound to 127.0.0.1:5000. "
        "nginx is the only public listener and proxies to it. The templates are in <code>automation/templates/</code>.</p>",
        "<h2>First run</h2>",
        term(log, "ANSIBLE_DEPRECATION", tail=22),
        "<h2>Second run (idempotency) and verification</h2>",
        term(log, "| tail -4", "systemctl is-active", "8301/healthz", "8302/stats"),
        "<h2>Observations</h2>",
        bullets(
            "First run: <b>changed=10</b> per node. Second run with no edits: <b>changed=0</b>. "
            "Ansible only changes what differs from the declared state, so re-running it is safe.",
            "Handlers restart the app and reload nginx only when their inputs change. "
            "On the second run neither handler fired.",
            "A <code>raw</code> task bootstraps Python first, because every other module needs Python on the node.",
            "Issues I hit and fixed: <code>become</code> failed because the node has no sudo (the docker connection already runs as root). "
            "The <code>pip</code> module needs <code>python3-packaging</code> on the node. "
            "A flaky network broke one pip download, so the task now retries 3 times.",
        ),
    ])


def q2():
    log = "q2-terraform.log"
    return "".join([
        "<h2>Configuration</h2>",
        config("infra/main.tf", "infra/main.tf"),
        "<h2>Init, validate, plan, apply</h2>",
        term(log, "docker build", "terraform version", "terraform init", "fmt -check"),
        term(log, "-out=tfplan", head=14, label="plan output (first lines; the full plan is in evidence/logs/q2-terraform.log)"),
        term(log, "apply -no-color -auto-approve tfplan", tail=8),
        term(log, "8310/healthz"),
        "<h2>Scaling from 2 to 4 replicas</h2>",
        term(log, "-var replicas=4", "8313/healthz", "state list"),
        "<h2>Scale back and drift check</h2>",
        term(log, "-var replicas=2", "detailed-exitcode"),
        "<h2>Observations</h2>",
        bullets(
            "Scaling is a single variable: <code>-var replicas=4</code> added exactly 2 containers "
            "(<b>2 added, 0 changed, 0 destroyed</b>), and each new container got the next free port automatically.",
            "<code>terraform plan -detailed-exitcode</code> returned <b>0</b> after the changes, "
            "so the real infrastructure matches the code exactly.",
            "My first attempt replaced <i>every</i> container on each scale. The plan showed <code>log_opts</code> "
            "\"forces replacement\": the Docker daemon adds default log options that are not in my config. "
            "Fixed with <code>lifecycle { ignore_changes = [log_opts] }</code>.",
            "Building the image inside Terraform hung on this engine, so the image is built with <code>docker build</code> first "
            "and Terraform reads it with a <code>docker_image</code> data source. Build and provisioning stay separate steps.",
            "The validation block rejects replica counts outside 1-10, so a typo cannot ask for hundreds of containers.",
        ),
    ])


def q3():
    log = "q3-monitoring.log"
    return "".join([
        "<h2>Instrumentation</h2>",
        config("service/web.py", "service/web.py (metrics)", "REQUESTS = Counter(", "log = logging"),
        config("service/web.py", "service/web.py (one hook observes every request)", "@app.after_request", '@app.get("/")'),
        "<p>Routes are labelled by their URL rule, not the raw path. Unknown URLs all share <code>route=\"unmatched\"</code>, "
        "so random URLs cannot create unlimited metric series (a unit test covers this).</p>",
        "<h2>Prometheus and Grafana</h2>",
        config("observability/prometheus.yml"),
        term(log, "up -d --build", "compose.yml ps", "8300/healthz"),
        "<p>The datasource and the dashboard are provisioned from files in <code>observability/grafana/</code>, "
        "so Grafana has the dashboard on first start with no manual clicks.</p>",
        "<h2>Verification after 60 s of traffic</h2>",
        term(log, "8300/metrics", "api/v1/targets", "api/v1/query", "api/health", "api/dashboards"),
        shot("q3-prometheus-targets", "Prometheus target health: both scrape targets UP"),
        shot("q3-prometheus-graph", "Prometheus query: request rate per route"),
        shot("q3-grafana-dashboard", "Provisioned Grafana dashboard under live traffic"),
        "<h2>Observations</h2>",
        bullets(
            "Both targets are UP and scraped every 5 s.",
            "The traffic script deliberately sends 2 bad requests in every 6 (a non-string <code>text</code> and an unknown URL). "
            "The error-ratio panel correctly shows about 33% and turns red, because its thresholds are 5% (orange) and 20% (red).",
            "The first dashboard showed p95 latency as a flat 4.75 ms. The default histogram buckets start at 5 ms, "
            "so every sub-millisecond request landed in the first bucket. Adding buckets from 0.5 ms shows the real "
            "p95 of about 0.48 ms.",
            "Requests to <code>/metrics</code> are not counted, so scraping does not inflate the request rate.",
        ),
    ])


def q6():
    log = "q6-testing.log"
    return "".join([
        "<h2>Unit tests</h2>",
        term(log, "pytest"),
        "<h2>Feature flag</h2>",
        config("service/web.py", "service/web.py (flag)", "FEATURE_TOP_WORDS = ", "LOG_FILE = "),
        config("service/web.py", "service/web.py (gated endpoint)", '@app.post("/stats/top")'),
        "<p>The same image is started twice. Only the environment variable differs.</p>",
        term(log, "--name flag-off", "--name flag-on", "8320/stats/top", "8321/stats/top"),
        "<div class='keep'>",
        shot("q6-ui-flag-off", "Flag off: only the Analyse button is rendered", small=True),
        shot("q6-ui-flag-on", "Flag on: the Top words button appears", small=True),
        "</div>",
        "<h2>Load test (ApacheBench)</h2>",
        term(log, "ab -q"),
        shot("q6-grafana-load-test", "Grafana during the load tests. The Q6 script ran twice (see the bug below), so each /healthz and /stats burst appears twice."),
        "<h2>Selenium browser test</h2>",
        config("e2e/test_ui_selenium.py", "e2e/test_ui_selenium.py (checks)", "try:"),
        term(log, "standalone-chromium", "4444/status", "test_ui_selenium"),
        "<div class='keep'>",
        shot("q6-selenium-analyse", "Screenshot taken by Selenium after clicking Analyse", small=True),
        shot("q6-selenium-top-words", "Screenshot taken by Selenium after clicking Top words", small=True),
        "</div>",
        "<h2>Bug found by the browser test</h2>",
        term("q6-selenium-first-run-bug.log", label="evidence/logs/q6-selenium-first-run-bug.log (first run)", tail=4),
        "<p>The unit tests passed, but the first Selenium run failed: clicking Analyse did nothing. "
        "The page script declared <code>const top</code>, and <code>top</code> is already a read-only global (<code>window.top</code>). "
        "So the whole script failed with a SyntaxError and no click handlers were attached. "
        "I renamed it to <code>topButton</code>, and the second run passed all three checks. "
        "Only a real browser could catch this bug.</p>",
        "<h2>Observations</h2>",
        bullets(
            "The flag toggles behaviour without a rebuild or a code change: <b>HTTP 404</b> with the flag off, "
            "<b>HTTP 200</b> with it on, from the same image.",
            "One gunicorn worker with 8 threads served about <b>4,000 req/s</b> on /healthz and <b>3,575 req/s</b> on POST /stats "
            "at concurrency 50, with 0 failed requests.",
            "At concurrency 200, throughput dropped to about 3,000 req/s and p99 rose from 23 ms to 110 ms. "
            "The service saturates and requests start to queue, but none fail.",
            "Grafana's server-side p95 stayed below 0.5 ms during the load, while ApacheBench measured a mean of 12.5 ms per request. "
            "The difference is time spent queued in front of the worker, which the in-app histogram cannot see.",
        ),
    ])


def q4():
    log = "q4-elk.log"
    return "".join([
        "<h2>Log format</h2>",
        "<p>The app writes one line per request to <code>/var/log/text-stats/app.log</code> on a Docker volume. "
        "Logstash mounts the same volume read-only. Requests that end in 4xx or 5xx are logged at WARNING.</p>",
        config("service/web.py", "service/web.py (log line)", "level = logging.WARNING", "return response"),
        "<h2>Logstash pipeline</h2>",
        config("observability/logstash/pipeline.conf"),
        "<p>Grok splits each line into typed fields (<code>status</code> as an integer, <code>duration_ms</code> as a float). "
        "The date filter replaces the ingest time with the time written in the log line.</p>",
        "<h2>Deploy the stack</h2>",
        term(log, "up -d elasticsearch", "_cluster/health >/dev/null", "compose.yml ps"),
        "<h2>Collection and parsing</h2>",
        term(log, "tail -3", "_cat/indices", "sort=@timestamp", "_grokparsefailure", '"aggs"', "wc -l", "unassigned_shards"),
        "<h2>Visualization in Kibana</h2>",
        term(log, "data_views"),
        shot("q4-kibana-discover", "Discover: parsed documents over the last hour; the two spikes are the Q6 load tests"),
        shot("q4-kibana-errors", "Query status >= 400, broken down by route: only /stats (400) and unmatched (404)"),
        shot("q4-kibana-document", "One document: the raw line (message) next to the fields grok extracted from it"),
        "<h2>Observations</h2>",
        bullets(
            "<b>No lost and no unparsed lines:</b> the log file had 86,198 lines and the index had 86,198 documents, "
            "with 0 <code>_grokparsefailure</code> tags.",
            "The level split (77,563 INFO / 8,632 WARNING) matches the traffic: the script sends 2 bad requests in every 6, "
            "and the load tests sent only good ones.",
            "Kibana's time column shows IST and the raw line shows UTC (20:01:20 becomes 01:31:20). "
            "Setting <code>timezone =&gt; \"UTC\"</code> in the date filter is what makes that correct; without it the events would be shifted.",
            "Routes come from Flask's URL rule, like the metrics labels, so every unknown URL is grouped as <code>unmatched</code>.",
            "Cluster health turns <b>yellow</b> once the index exists. The default 1 replica cannot be placed on a single node. "
            "This is expected for a one-node lab cluster.",
            "Security is disabled in Elasticsearch, so Kibana shows a \"your data is not secure\" warning. "
            "Ports bind to 127.0.0.1 only.",
        ),
    ])


def q5():
    gates = (
        "<table><tr><th>Build</th><th>Commit</th><th>Unit tests</th><th>Dependency audit</th><th>Bandit</th>"
        "<th>Trivy fs</th><th>Trivy image</th><th>Result</th></tr>"
        "<tr><td>#1</td><td>6a57381</td><td colspan='5'>pipeline/Jenkinsfile not pushed yet (setup error)</td><td>FAILURE</td></tr>"
        "<tr><td>#2</td><td>2b3d7df</td><td>9 passed</td><td><b>20 vulns</b> in flask, pytest, urllib3</td><td colspan='3'>skipped</td><td>BLOCKED</td></tr>"
        "<tr><td>#3</td><td>9b358b9</td><td>9 passed</td><td>clean</td><td>clean</td><td><b>4 HIGH</b> Dockerfile misconfigs</td><td>skipped</td><td>BLOCKED</td></tr>"
        "<tr><td>#4</td><td>8a039d2</td><td>9 passed</td><td>clean</td><td>clean</td><td>clean</td><td><b>5 HIGH</b> CVEs</td><td>BLOCKED</td></tr>"
        "<tr><td>#5</td><td>7064c7e</td><td>9 passed</td><td>clean</td><td>clean</td><td>clean</td><td>clean</td><td><b>SUCCESS</b></td></tr>"
        "</table>"
    )
    return "".join([
        "<h2>Pipeline</h2>",
        "<p>Jenkins runs in a container on the lab machine (<code>pipeline/Dockerfile</code>, <code>pipeline/compose.yml</code>). "
        "It polls the GitHub repository every 2 minutes. Builds 3, 4 and 5 were started by \"an SCM change\", with no manual trigger. "
        "Each scanner exits non-zero on a finding, which fails its stage and skips every later stage.</p>",
        config("pipeline/Jenkinsfile"),
        "<h2>Build history: every gate caught something real</h2>",
        gates,
        shot("q5-jenkins-job", "Jenkins job: builds 1-4 failed, build 5 passed"),
        "<h3>Build 2: dependency audit (pip-audit)</h3>",
        "<p>The requirements were copied from Lab 1, which pinned flask 3.1.0 and pytest 8.3.4. Both now have published advisories. "
        "urllib3 2.4.0 was pulled in by selenium 4.33. Fix: flask 3.1.3, pytest 9.2.0, and selenium 4.52 (which requires urllib3 &gt;= 2.6.3).</p>",
        shot("q5-jenkins-build2-console", "Build 2 console: 20 known vulnerabilities in 3 packages, later stages skipped"),
        "<h3>Build 3: misconfiguration scan (Trivy fs)</h3>",
        "<p>The app Dockerfile passed, but both lab infrastructure images had 2 HIGH findings each. "
        "DS-0029 (missing <code>--no-install-recommends</code>) was fixed in both. "
        "DS-0002 (runs as root) is a real requirement for those two images: the Ansible node runs systemd as PID 1, "
        "and Jenkins needs the Docker socket. It is accepted in <code>.trivyignore.yaml</code>, scoped to those two files, "
        "each with a written reason. The application image gets no exceptions.</p>",
        shot("q5-jenkins-build3-console", "Build 3 console: Trivy misconfiguration findings"),
        config(".trivyignore.yaml"),
        "<h3>Build 4: image scan (Trivy image)</h3>",
        "<p>The image had 5 HIGH CVEs in msgpack, urllib3 and setuptools. None of these are dependencies of the app: "
        "they are copies vendored inside pip in the Python base image. The app never runs pip, so the Dockerfile now "
        "uninstalls it after installing the requirements. This removes the CVEs and shrinks the attack surface.</p>",
        "<table><tr><th>Package (vendored in pip)</th><th>Installed</th><th>Finding</th><th>Fixed in</th></tr>"
        "<tr><td>msgpack</td><td>1.1.2</td><td>CVE-2026-114613 (DoS), GHSA-6v7p-g79w-8964 (out-of-bounds read)</td><td>1.2.3 / 1.2.1</td></tr>"
        "<tr><td>setuptools (pkg_resources)</td><td>70.3.0</td><td>CVE-2025-47273 (path traversal)</td><td>78.1.1</td></tr>"
        "<tr><td>urllib3</td><td>2.7.0</td><td>CVE-2026-97687, CVE-2026-97689</td><td>2.8.0</td></tr></table>"
        "<p class='label'>Summary of the local reproduction; full output in evidence/logs/q5-image-scan-before-fix.log</p>",
        shot("q5-jenkins-build4-console", "Build 4 console: image scan blocks on 5 HIGH CVEs"),
        "<h3>Build 5: all gates pass</h3>",
        shot("q5-jenkins-build5-console", "Build 5: pip-audit and bandit clean, Trivy fs starting"),
        shot("q5-jenkins-build5-end", "Build 5: image scan clean, Finished: SUCCESS"),
        "<h2>Same scans run locally after the fixes</h2>",
        term("q5-local-scans.log", "pip-audit", "bandit", "docker build"),
        term("q5-local-scans.log", "trivy fs", tail=14),
        "<p>Bandit prints nothing with <code>-q</code> when it finds no issues, and its exit code is 0.</p>",
        "<h2>Secure pipeline practices used</h2>",
        bullets(
            "<b>Fail closed:</b> every scanner uses a non-zero exit code on findings, so nothing vulnerable reaches the image stage.",
            "<b>Shift left:</b> the cheap checks (tests, dependency audit, static analysis) run before the image is built.",
            "<b>Pinned versions:</b> every Python dependency and tool version (Trivy 0.76.2, Terraform 1.17.1) is pinned, "
            "so a build is reproducible and a scan result refers to known versions.",
            "<b>Accepted risk is explicit:</b> exceptions live in a reviewed file with a reason, not in a flag that silences everything.",
            "<b>Least privilege in the product:</b> the app image runs as an unprivileged user, has no pip, and binds only the port it needs.",
            "<b>Secret scanning:</b> Trivy's secret scanner runs on every build. The repository is public, so this matters.",
        ),
    ])


ARCHITECTURE = """
<svg viewBox="0 0 720 300" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial, sans-serif" font-size="11">
  <defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 z" fill="#444"/></marker></defs>
  <g fill="#fff" stroke="#333" stroke-width="1.2">
    <rect x="10" y="20" width="120" height="44" rx="6"/>
    <rect x="170" y="20" width="120" height="44" rx="6"/>
    <rect x="330" y="20" width="180" height="44" rx="6"/>
    <rect x="550" y="20" width="160" height="44" rx="6"/>
    <rect x="10" y="130" width="160" height="50" rx="6"/>
    <rect x="200" y="130" width="160" height="50" rx="6"/>
    <rect x="390" y="120" width="320" height="70" rx="6" stroke-dasharray="4 3"/>
    <rect x="10" y="230" width="160" height="50" rx="6"/>
    <rect x="200" y="230" width="160" height="50" rx="6"/>
    <rect x="390" y="230" width="150" height="50" rx="6"/>
    <rect x="560" y="230" width="150" height="50" rx="6"/>
  </g>
  <g text-anchor="middle" fill="#111">
    <text x="70" y="40" font-weight="700">Developer</text><text x="70" y="55">git push</text>
    <text x="230" y="40" font-weight="700">GitHub</text><text x="230" y="55">public repo</text>
    <text x="420" y="40" font-weight="700">Jenkins (pollSCM)</text><text x="420" y="55">tests, pip-audit, bandit, trivy</text>
    <text x="630" y="40" font-weight="700">text-stats image</text><text x="630" y="55">only if every gate passes</text>
    <text x="90" y="150" font-weight="700">Ansible</text><text x="90" y="166">2 systemd nodes + nginx</text>
    <text x="280" y="150" font-weight="700">Terraform</text><text x="280" y="166">N app containers</text>
    <text x="550" y="140" font-weight="700">text-stats app (compose)</text>
    <text x="550" y="156">/metrics (Prometheus format)</text><text x="550" y="172">app.log on a shared volume</text>
    <text x="90" y="250" font-weight="700">Selenium + ab</text><text x="90" y="266">browser and load tests</text>
    <text x="280" y="250" font-weight="700">Feature flag</text><text x="280" y="266">FEATURE_TOP_WORDS env</text>
    <text x="465" y="250" font-weight="700">Prometheus</text><text x="465" y="266">-> Grafana</text>
    <text x="635" y="250" font-weight="700">Logstash -> ES</text><text x="635" y="266">-> Kibana</text>
  </g>
  <g stroke="#444" stroke-width="1.2" fill="none" marker-end="url(#a)">
    <path d="M130,42 H168"/><path d="M290,42 H328"/><path d="M510,42 H548"/>
    <path d="M465,190 V228"/><path d="M635,190 V228"/>
    <path d="M170,255 H198"/><path d="M360,255 C380,255 380,180 388,170"/>
  </g>
  <text x="10" y="110" fill="#555">Automation</text><text x="390" y="110" fill="#555">Observed system</text>
  <text x="10" y="222" fill="#555">Testing</text><text x="390" y="222" fill="#555">Observability</text>
</svg>
"""


def q7():
    return "".join([
        "<h2>1. Objective</h2>",
        "<p>Take the text statistics service from Lab 1 and build an automated, observable and secure workflow around it. "
        "Ansible and Terraform handle automation, Prometheus and Grafana collect metrics, and the ELK stack centralizes logs. "
        "A Jenkins pipeline blocks insecure changes, and feature flags, load tests and browser tests check behaviour.</p>",
        "<h2>2. Environment and tools</h2>",
        term("q7-environment.log"),
        "<p>Monitoring and logging images: Prometheus v3.16.0, Grafana 13.3.0, and Elasticsearch, Logstash and Kibana 9.5.6. "
        "Every port binds to 127.0.0.1 on the lab machine.</p>",
        "<h2>3. Architecture</h2>",
        ARCHITECTURE,
        "<h2>4. Automation</h2>",
        bullets(
            "<b>Ansible (Q1):</b> one playbook takes two bare Ubuntu nodes to a running service behind nginx. "
            "First run: changed=10 per node. Second run: changed=0.",
            "<b>Terraform (Q2):</b> container count is one variable. Scaling 2 to 4 added 2 containers and destroyed 0. "
            "A final <code>plan -detailed-exitcode</code> returned 0 (no drift).",
            "<b>Pipeline (Q5):</b> Jenkins polls GitHub and runs every gate on each push, with no manual trigger.",
        ),
        "<h2>5. Observability</h2>",
        bullets(
            "<b>Metrics (Q3):</b> request counter by method, route and status, a latency histogram, and words processed. "
            "Prometheus scrapes every 5 s, and Grafana is provisioned from files with 6 panels.",
            "<b>Logs (Q4):</b> one structured line per request, shipped by Logstash, parsed with grok into level, method, "
            "route, status and duration fields, and explored in Kibana.",
            "Metrics and logs answer different questions. Grafana shows <i>how much</i> and <i>how fast</i>. "
            "Kibana shows <i>which request</i>: for example, every 400 for a non-string <code>text</code>.",
        ),
        shot("q3-grafana-dashboard", "Grafana dashboard under traffic (Q3)"),
        shot("q4-kibana-discover", "Kibana Discover over the parsed application logs (Q4)"),
        "<h2>6. Security findings</h2>",
        "<table><tr><th>Gate</th><th>Finding</th><th>Action</th></tr>"
        "<tr><td>pip-audit (build 2)</td><td>flask 3.1.0, pytest 8.3.4, urllib3 2.4.0: 20 advisories</td><td>Upgraded to patched versions</td></tr>"
        "<tr><td>Trivy misconfig (build 3)</td><td>DS-0029 x2, DS-0002 x2 in the lab infrastructure Dockerfiles</td>"
        "<td>Fixed DS-0029; DS-0002 accepted with reasons, scoped to the 2 files</td></tr>"
        "<tr><td>Trivy image (build 4)</td><td>5 HIGH CVEs in pip's vendored msgpack, urllib3 and setuptools</td><td>Removed pip from the runtime image</td></tr>"
        "<tr><td>Bandit (all builds)</td><td>No issues in <code>service/</code></td><td>-</td></tr>"
        "<tr><td>Trivy secrets (all builds)</td><td>No secrets in the public repository</td><td>-</td></tr></table>",
        shot("q5-jenkins-job", "Jenkins: builds 2-4 blocked by real findings, build 5 passed"),
        "<h2>7. Testing</h2>",
        bullets(
            "9 unit tests, including metric label cardinality and both states of the feature flag.",
            "The feature flag toggles <code>/stats/top</code> between HTTP 404 and 200 without a rebuild.",
            "ApacheBench: about 4,000 req/s at concurrency 50 with 0 failures. "
            "At concurrency 200, p99 latency rose to 110 ms, while server-side p95 stayed under 0.5 ms (time spent queueing).",
            "Selenium found a bug the unit tests could not: a <code>const top</code> collision with <code>window.top</code> "
            "stopped the page script from loading.",
        ),
        "<h2>8. Observations</h2>",
        bullets(
            "Every gate caught something real. Dependencies copied from an earlier lab had picked up advisories, "
            "and the biggest image finding came from a tool (pip) the app never uses.",
            "Defaults hide things: Docker's injected log options made Terraform replace containers, and Prometheus' default "
            "buckets flattened p95 latency. Both looked fine until they were checked against real data.",
            "Structured log lines are what make ELK useful. Grok turns each line into typed fields, so Kibana can count "
            "and filter instead of doing full-text search.",
            "Security settings are deliberately relaxed for the lab (no auth on Elasticsearch and Jenkins, anonymous Grafana viewer). "
            "Every port binds to localhost to keep that safe. Production would need auth and TLS.",
        ),
    ])


REPORTS = {
    1: ("q1-ansible-configuration", "Ansible configuration management",
        "Configure infrastructure and automate application configuration using Ansible by writing playbooks "
        "and applying them to target nodes.", q1),
    2: ("q2-terraform-iac", "Terraform infrastructure as code",
        "Provision scalable infrastructure using Terraform (Infrastructure as Code): write configuration files, "
        "initialize, plan, and apply the infrastructure.", q2),
    3: ("q3-prometheus-grafana", "Prometheus and Grafana monitoring",
        "Set up monitoring using Prometheus and visualize metrics using Grafana dashboards for a target "
        "application or system.", q3),
    4: ("q4-elk-centralized-logging", "Centralized logging with the ELK stack",
        "Implement centralized logging using the ELK stack and demonstrate log collection, parsing, and "
        "visualization in Kibana.", q4),
    5: ("q5-devsecops-pipeline", "DevSecOps pipeline",
        "Integrate security into the CI/CD pipeline (DevSecOps): perform vulnerability/dependency scanning and "
        "demonstrate secure pipeline practices.", q5),
    6: ("q6-feature-flags-testing", "Feature flags, load testing and Selenium",
        "Implement feature flags, perform load testing, and demonstrate Selenium-based automated testing; "
        "record commands, configurations, screenshots, and observations.", q6),
    7: ("q7-monitoring-devsecops-report", "Monitoring, logging and DevSecOps report",
        "Prepare a monitoring, logging, and DevSecOps report describing the automation, observability setup, "
        "security findings, and observations with screenshots.", q7),
}
