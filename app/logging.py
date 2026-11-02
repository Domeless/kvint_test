import json
import logging
import logging.config
import re
import sys
import traceback
from pathlib import Path
from typing import Any

import structlog
from structlog.types import EventDict


def add_component(logger: Any, method_name: str, event: EventDict) -> EventDict:
    event.setdefault("component", "app")
    return event


def safe_exception(logger: Any, method_name: str, event: EventDict) -> EventDict:
    """Keep exception messages and frame locations without local variable values."""
    exc_info = event.pop("exc_info", None)
    include_error_message = event.pop("include_error_message", True)
    if exc_info:
        if isinstance(exc_info, BaseException):
            exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
        elif not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()
        if exc_info[0] is not None:
            event["error_type"] = exc_info[0].__name__
            if include_error_message:
                event["error"] = str(exc_info[1])
            event["exception"] = [
                {"file": frame.filename, "line": frame.lineno, "function": frame.name}
                for frame in traceback.extract_tb(exc_info[2])
            ]
    event.pop("stack_info", None)
    return event


def redact_credentials(logger: Any, method_name: str, event: EventDict) -> EventDict:
    """Mask URL credentials in log and error messages."""
    for field in ("event", "error"):
        if isinstance(event.get(field), str):
            event[field] = re.sub(r"(\w+://)[^\s/@]+(?::[^\s/@]*)?@", r"\1***@", event[field])
    return event


def shared_processors() -> list[Any]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_component,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        safe_exception,
    ]


def make_formatter() -> logging.Formatter:
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors(),
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            redact_credentials,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
    )


def configure_logging() -> None:
    """Configure one JSON pipeline for structlog, standard logging and Uvicorn."""
    config = json.loads(Path(__file__).with_name("logging.json").read_text(encoding="utf-8"))
    logging.config.dictConfig(config)
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
