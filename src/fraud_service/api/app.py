import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.api.routes import router
from fraud_service.config import Settings
from fraud_service.domain.entities import Channel, Transaction
from fraud_service.service.scorer import FraudScorer

log = logging.getLogger("fraud_service")


def _error(request, status, code, message, details=None, headers=None):
    body = {
        "code": code,
        "message": message,
        "trace_id": getattr(request.state, "trace_id", "unknown"),
    }
    if details is not None:
        body["details"] = details

    return JSONResponse(
        status_code=status,
        content={"error": body},
        headers=headers,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    logging.basicConfig(level=settings.log_level)

    app.state.settings = settings
    app.state.started_at = datetime.now(UTC)

    start = time.perf_counter()
    model = SklearnModel.load(settings.model_path)

    warmup = Transaction(
        transaction_id="WARMUP-0000",
        amount_sar=100.0,
        channel=Channel.POS,
        merchant_category="GROCERY",
        customer_id="warmup",
        timestamp=datetime.now(UTC),
    )
    model.predict_proba(warmup.to_features())

    app.state.scorer = FraudScorer(
        model=model,
        block_threshold=settings.block_threshold,
    )

    log.info(
        "model loaded: version=%s seconds=%.3f",
        model.model_version,
        time.perf_counter() - start,
    )
    yield
    log.info("shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Fraud Scoring Service",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(router, prefix="/v1")

    @app.middleware("http")
    async def trace_and_time(request: Request, call_next):
        trace_id = request.headers.get(
            "X-Trace-Id", uuid.uuid4().hex[:16]
        )
        request.state.trace_id = trace_id

        start = time.perf_counter()
        response = await call_next(request)

        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Response-Time-Ms"] = str(
            round((time.perf_counter() - start) * 1000, 1)
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [
            {
                "field": ".".join(map(str, err["loc"][1:])) or "body",
                "problem": err["msg"],
            }
            for err in exc.errors()
        ]
        return _error(
            request, 422, "INVALID_REQUEST",
            "Request body failed validation",
            details=details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        code = {
            404: "NOT_FOUND",
            503: "MODEL_UNAVAILABLE",
        }.get(exc.status_code, "HTTP_ERROR")

        return _error(
            request,
            exc.status_code,
            code,
            "Requested resource is unavailable",
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        log.exception("Unhandled error", exc_info=exc)
        return _error(
            request, 500, "INTERNAL_ERROR",
            "Unexpected error; contact support with trace_id",
        )

    return app
