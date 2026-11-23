import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fraud_service.api.app import create_app
from fraud_service.service.scorer import FraudScorer

PAYLOAD_DIR = Path("payloads")
SAMPLE = json.loads(
    (PAYLOAD_DIR / "sample.json").read_text(encoding="utf-8")
)
BAD_CASES = sorted((PAYLOAD_DIR / "malformed").glob("*.json"))


@pytest.mark.integration
def test_prediction_contract(client_factory):
    response = client_factory(probability=0.93).post(
        "/v1/predict", json=SAMPLE
    )
    assert response.status_code == 200

    data = response.json()
    assert set(data) == {
        "transaction_id",
        "fraud_probability",
        "decision",
        "model_version",
        "trace_id",
    }
    assert data["decision"] == "block"
    assert data["model_version"] == "test-1"
    assert response.headers["X-Trace-Id"] == data["trace_id"]
    assert response.headers["X-Model-Version"] == "test-1"


@pytest.mark.integration
def test_custom_trace_id(client_factory):
    response = client_factory().post(
        "/v1/predict",
        json=SAMPLE,
        headers={"X-Trace-Id": "test-trace-123"},
    )
    assert response.status_code == 200
    assert response.json()["trace_id"] == "test-trace-123"


@pytest.mark.integration
@pytest.mark.parametrize("case", BAD_CASES, ids=lambda p: p.stem)
def test_invalid_requests(case, client_factory):
    response = client_factory().post(
        "/v1/predict",
        content=case.read_bytes(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422, case.name
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.integration
def test_validation_does_not_reveal_input(client_factory):
    invalid = {**SAMPLE, "amount_sar": -987654}
    response = client_factory().post("/v1/predict", json=invalid)

    assert response.status_code == 422
    assert "987654" not in response.text
    assert response.json()["error"]["details"][0]["field"] == "amount_sar"


@pytest.mark.integration
def test_internal_errors_are_hidden(client_factory, monkeypatch):
    def fail_scoring(self, transaction):
        raise RuntimeError("private internal diagnostic")

    monkeypatch.setattr(FraudScorer, "score", fail_scoring)

    response = client_factory().post("/v1/predict", json=SAMPLE)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "private internal diagnostic" not in response.text


@pytest.mark.integration
def test_model_unavailable():
    client = TestClient(create_app(), raise_server_exceptions=False)

    responses = [
        client.get("/v1/ready"),
        client.post("/v1/predict", json=SAMPLE),
    ]
    for response in responses:
        assert response.status_code == 503
        assert response.headers["Retry-After"] == "5"
        assert response.json()["error"]["code"] == "MODEL_UNAVAILABLE"


@pytest.mark.integration
def test_real_application_startup(monkeypatch):
    monkeypatch.setenv(
        "FRAUD_MODEL_PATH", "models/fraud_xgb_v3.joblib"
    )

    with TestClient(create_app()) as client:
        assert client.get("/v1/ready").status_code == 200
        assert client.get("/v1/health").json()["status"] == "ok"
        response = client.post("/v1/predict", json=SAMPLE)

    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "v3.2.0"
    assert 0 <= data["fraud_probability"] <= 1
