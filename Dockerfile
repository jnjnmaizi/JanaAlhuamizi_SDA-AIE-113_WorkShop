# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

COPY requirements.lock .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.lock

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

RUN useradd --create-home --uid 10001 appuser

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY models/fraud_xgb_v3.joblib /models/fraud_xgb_v3.joblib
COPY src/ /app/src

ARG GIT_SHA=dev
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    FRAUD_MODEL_PATH=/models/fraud_xgb_v3.joblib \
    FRAUD_GIT_SHA=$GIT_SHA

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/v1/ready || exit 1

CMD ["uvicorn", "fraud_service.api.app:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]
