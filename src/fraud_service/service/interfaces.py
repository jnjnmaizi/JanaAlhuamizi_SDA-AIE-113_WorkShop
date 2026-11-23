from typing import Protocol

from fraud_service.domain.entities import FeatureVector, RawScore


class Model(Protocol):
    model_version: str

    def predict_proba(self, features: FeatureVector) -> RawScore:
        ...
