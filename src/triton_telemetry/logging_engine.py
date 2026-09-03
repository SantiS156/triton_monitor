from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any


class UTCJSONFormatter(logging.Formatter):
    """
    Formatea los registros de logging como JSON estructurado.

    La marca de tiempo se genera en UTC y utiliza el formato
    ISO 8601 estricto con sufijo 'Z'.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": (
                datetime.now(timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "thread": record.threadName,
        }

        if record.exc_info is not None:
            exception = record.exc_info[1]

            if isinstance(exception, Exception):
                payload["exception"] = serialize_exception(
                    exception
                )

        trace_id = getattr(record, "trace_id", None)

        if trace_id is not None:
            payload["trace_id"] = trace_id

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def serialize_exception(exception: Exception) -> dict[str, Any]:
    """
    Serializa una excepción conservando toda la información
    relevante de su traceback.

    Si se trata de un ExceptionGroup, cada excepción hija se
    serializa recursivamente.

    También se conservan:
    - __cause__
    - __context__
    - traceback
    - tipo
    - módulo
    - mensaje
    """

    serialized: dict[str, Any] = {
        "type": type(exception).__name__,
        "module": type(exception).__module__,
        "message": str(exception),
    }

    if exception.__traceback__ is not None:
        serialized["traceback"] = "".join(
            traceback.format_exception(
                type(exception),
                exception,
                exception.__traceback__,
            )
        )

    if isinstance(exception, ExceptionGroup):
        serialized["exceptions"] = [
            serialize_exception(child)
            for child in exception.exceptions
            if isinstance(child, Exception)
        ]

    if exception.__cause__ is not None:
        serialized["cause"] = serialize_exception(
            exception.__cause__
        )

    if (
        exception.__context__ is not None
        and not exception.__suppress_context__
        and isinstance(exception.__context__, Exception)
    ):
        serialized["context"] = serialize_exception(
            exception.__context__
        )

    return serialized


class LoggingEngine:
    """
    Motor de logging estructurado.

    Este componente se ocupa exclusivamente de:
    - crear el logger;
    - aplicar el formato JSON;
    - generar timestamps UTC;
    - serializar excepciones.

    La escritura física en disco debe permanecer fuera de este
    módulo y ser gestionada por el sistema de QueueHandler /
    QueueListener.
    """

    LOGGER_NAME = "triton_telemetry"

    def __init__(
        self,
        level: int = logging.INFO,
    ) -> None:
        self.level = level
        self.logger = logging.getLogger(self.LOGGER_NAME)

    def configure(
        self,
        handler: logging.Handler,
    ) -> logging.Logger:
        """
        Configura el logger utilizando el handler recibido.

        El handler puede ser un QueueHandler proporcionado por
        storage.py.
        """

        handler.setLevel(self.level)

        self.logger.setLevel(self.level)
        self.logger.propagate = False

        if handler not in self.logger.handlers:
            self.logger.addHandler(handler)

        return self.logger

    def get_logger(self) -> logging.Logger:
        """
        Devuelve el logger de telemetría.
        """

        return self.logger


def create_logging_engine(
    level: int = logging.INFO,
) -> LoggingEngine:
    """
    Crea una instancia del motor de logging.
    """

    return LoggingEngine(level=level)
