import pytest

from service.web import app, text_stats


@pytest.fixture
def client():
    return app.test_client()


def test_healthz_reports_healthy(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json["healthy"] is True


def test_text_stats_counts_unique_words_case_insensitively():
    assert text_stats("Build test build") == {"characters": 16, "words": 3, "unique_words": 2}


def test_stats_endpoint_returns_counts(client):
    response = client.post("/stats", json={"text": "ship it"})
    assert response.status_code == 200
    assert response.json["words"] == 2


@pytest.mark.parametrize("body", [{}, {"text": 42}])
def test_stats_endpoint_rejects_invalid_text(client, body):
    assert client.post("/stats", json=body).status_code == 400


def test_metrics_exposes_request_counter(client):
    client.get("/healthz")
    body = client.get("/metrics").get_data(as_text=True)
    assert 'textstats_http_requests_total{method="GET",route="/healthz",status="200"}' in body


def test_unknown_urls_share_one_metric_label(client):
    client.get("/no-such-page")
    body = client.get("/metrics").get_data(as_text=True)
    assert 'route="unmatched"' in body
    assert "no-such-page" not in body


def test_top_words_hidden_when_flag_off(client, monkeypatch):
    monkeypatch.setattr("service.web.FEATURE_TOP_WORDS", False)
    assert client.post("/stats/top", json={"text": "a a b"}).status_code == 404
    assert 'id="top"' not in client.get("/ui").get_data(as_text=True)


def test_top_words_served_when_flag_on(client, monkeypatch):
    monkeypatch.setattr("service.web.FEATURE_TOP_WORDS", True)
    response = client.post("/stats/top", json={"text": "Ship ship it"})
    assert response.json["top_words"][0] == {"word": "ship", "count": 2}
    assert 'id="top"' in client.get("/ui").get_data(as_text=True)
