from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from fraud_service.domain.entities import FeatureVector, RawScore


class SklearnModel:
    def __init__(self, pipeline: Any, model_version: str) -> None:
        self._pipeline = pipeline
        self.model_version = model_version

    @classmethod
    def load(cls, path: Path) -> "SklearnModel":
        saved_model = joblib.load(path)
        return cls(
            pipeline=saved_model["pipeline"],
            model_version=saved_model["version"],
        )

    def predict_proba(self, features: FeatureVector) -> RawScore:
        data = pd.DataFrame([features.values])
        probability = float(self._pipeline.predict_proba(data)[0, 1])
        return RawScore(value=probability)
