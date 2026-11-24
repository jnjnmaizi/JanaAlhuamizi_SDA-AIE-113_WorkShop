import math
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Channel(StrEnum):
    POS = "pos"
    ECOM = "ecom"
    ATM = "atm"
    TRANSFER = "transfer"


class FeatureVector(BaseModel):
    values: dict[str, float | int | str]


class Transaction(BaseModel):
    transaction_id: str = Field(min_length=8)
    amount_sar: float = Field(gt=0)
    channel: Channel
    merchant_category: str
    customer_id: str
    timestamp: datetime

    @field_validator("merchant_category")
    @classmethod
    def normalise_mcc(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "_")

    @field_validator("timestamp")
    @classmethod
    def normalise_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value.astimezone(UTC)

    def to_features(self) -> FeatureVector:
        hour = self.timestamp.hour
        return FeatureVector(values={
            "amount_log": round(math.log1p(self.amount_sar), 6),
            "channel": self.channel.value,
            "mcc": self.merchant_category,
            "hour_of_day": hour,
            "is_night": int(hour < 6),
        })


class RawScore(BaseModel):
    value: float = Field(ge=0, le=1)


class Decision(StrEnum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


class FraudScore(BaseModel):
    transaction_id: str
    probability: float
    decision: Decision
    model_version: str
