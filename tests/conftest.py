from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fraud_service.api.app import create_app
from fraud_service.api.routes import get_scorer
from fraud_service.domain.entities import FeatureVector, RawScore, Transaction
from fraud_service.service.scorer import FraudScorer

BASE_TXN = {
    "transaction_id": "TXN-TEST-0001",
    "amount_sar": 250.0,
    "channel": "ecom",
    "merchant_category": "electronics",
    "customer_id": "CUST-77",
    "timestamp": datetime(2026, 7, 5, 3, 30, tzinfo=UTC),
}


class ConstantModel:
    def __init__(self, p: float, version: str = "test-1") -> None:
        self._p = p
        self.model_version = version

    def predict_proba(self, features: FeatureVector) -> RawScore:
        return RawScore(value=self._p)


@pytest.fixture
def make_txn():
    def create(**overrides) -> Transaction:
        return Transaction(**{**BASE_TXN, **overrides})

    return create


@pytest.fixture
def sample_txn(make_txn):
    return make_txn()


@pytest.fixture
def client_factory():
    def create(probability: float = 0.10, threshold: float = 0.85):
        app = create_app()
        scorer = FraudScorer(
            model=ConstantModel(probability),
            block_threshold=threshold,
        )
        app.dependency_overrides[get_scorer] = lambda: scorer
        return TestClient(app, raise_server_exceptions=False)

    return create


@pytest.fixture(scope="session")
def real_model():
    from fraud_service.adapters.sklearn_model import SklearnModel

    return SklearnModel.load(Path("models/fraud_xgb_v3.joblib"))
