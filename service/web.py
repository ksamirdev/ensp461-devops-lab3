"""Text statistics service: Lab 1 app extended with metrics, logs and a feature flag."""
import logging
import os
import time
from collections import Counter as WordCounter

from flask import Flask, g, jsonify, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

RELEASE = os.environ.get("RELEASE", "3.0.0")
FEATURE_TOP_WORDS = os.environ.get("FEATURE_TOP_WORDS", "false").lower() == "true"
LOG_FILE = os.environ.get("LOG_FILE")

app = Flask(__name__)

REQUESTS = Counter(
    "textstats_http_requests_total", "HTTP requests served", ["method", "route", "status"]
)
LATENCY = Histogram(
    "textstats_http_request_duration_seconds",
    "Request latency",
    ["route"],
    buckets=(0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1),
)
WORDS = Counter("textstats_words_processed_total", "Words analysed by /stats")

log = logging.getLogger("textstats")
log.setLevel(logging.INFO)
_handlers = [logging.StreamHandler()]
if LOG_FILE:
    _handlers.append(logging.FileHandler(LOG_FILE))
for _handler in _handlers:
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    log.addHandler(_handler)


def text_stats(text):
    words = text.split()
    return {
        "characters": len(text),
        "words": len(words),
        "unique_words": len({w.lower() for w in words}),
    }


def top_words(text, limit=3):
    counts = WordCounter(w.lower() for w in text.split())
    return [{"word": word, "count": count} for word, count in counts.most_common(limit)]


def read_text():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text")
    return text if isinstance(text, str) else None


@app.before_request
def start_timer():
    g.started = time.perf_counter()


@app.after_request
def observe(response):
    if request.path == "/metrics":
        return response
    # url_rule, not path, so unknown URLs cannot create unbounded label values
    route = request.url_rule.rule if request.url_rule else "unmatched"
    elapsed = time.perf_counter() - g.started
    REQUESTS.labels(request.method, route, str(response.status_code)).inc()
    LATENCY.labels(route).observe(elapsed)
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    log.log(
        level,
        "method=%s path=%s status=%s duration_ms=%.2f",
        request.method, route, response.status_code, elapsed * 1000,
    )
    return response


@app.get("/")
def home():
    return jsonify(service="text-stats", release=RELEASE)


@app.get("/healthz")
def healthz():
    return jsonify(healthy=True, release=RELEASE)


@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.get("/ui")
def ui():
    return render_template("ui.html", release=RELEASE, top_words_enabled=FEATURE_TOP_WORDS)


@app.post("/stats")
def stats():
    text = read_text()
    if text is None:
        return jsonify(error="JSON field 'text' must be a string"), 400
    result = text_stats(text)
    WORDS.inc(result["words"])
    return jsonify(result)


@app.post("/stats/top")
def stats_top():
    if not FEATURE_TOP_WORDS:
        return jsonify(error="feature 'top_words' is disabled"), 404
    text = read_text()
    if text is None:
        return jsonify(error="JSON field 'text' must be a string"), 400
    return jsonify(top_words=top_words(text))
