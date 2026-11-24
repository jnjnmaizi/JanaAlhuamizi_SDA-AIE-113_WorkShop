from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from fraud_service.domain.entities import Channel, Decision, Transaction


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=8, max_length=64)
    amount_sar: float = Field(gt=0, le=1_000_000)
    channel: Channel
    merchant_category: str = Field(min_length=2, max_length=40)
    customer_id: str = Field(min_length=4, max_length=64)
    timestamp: AwareDatetime

    @field_validator("timestamp", mode="before")
    @classmethod
    def require_timestamp_string(cls, value: object) -> object:
        if not isinstance(value, str):
            raise ValueError("timestamp must be an ISO-8601 string with a timezone")  # noqa: TRY004 - Pydantic requires ValueError for a 422
        return value

    def to_domain(self) -> Transaction:
        return Transaction(**self.model_dump())


class PredictResponse(BaseModel):
    transaction_id: str
    fraud_probability: float = Field(ge=0, le=1)
    decision: Decision
    model_version: str
    trace_id: str


class ErrorBody(BaseModel):
    code: str
    message: str
    trace_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    git_sha: str
    started_at: datetime
