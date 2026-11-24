"""JSON logs to stdout. The platform owns shipping and retention."""
import logging
import sys
from typing import Any

import structlog
from structlog.typing import EventDict, WrappedLogger

SENSITIVE_KEYS = {"password", "token", "secret", "authorization",
                  "registry_token", "national_id", "card_number", "redis_url", "api_key"}


def _mask_sensitive(logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
    """Defensive masking: even if someone logs a secret, it leaves masked."""
    def scrub(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "***MASKED***" if str(key).lower() in SENSITIVE_KEYS else scrub(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [scrub(item) for item in value]
        return value

    return scrub(event_dict)


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(stream=sys.stdout, level=level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,      # trace_id bound per request
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),   # always UTC
            _mask_sensitive,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
    )


def get_logger(name: str) -> Any:
    return structlog.get_logger(name)
