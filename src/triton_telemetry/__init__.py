"""API pública del paquete de telemetría Tritón."""

from .core import (
    obtener_estado_aws,
    obtener_estado_azure,
    obtener_estado_gcp,
    obtener_nodo_demorado,
    obtener_nodo_error,
    obtener_todos_los_estados,
)

from .exceptions import (
    TritonError,
    ProviderTimeoutError,
    CorruptedPayloadError,
    NetworkPeeringError,
)

from .sanitizer import (
    validate_timeout,
    validate_cluster,
)

from .storage import (
    start_logging,
    stop_logging,
    get_logger,
)

__all__ = [
    # Core
    "obtener_estado_aws",
    "obtener_estado_azure",
    "obtener_estado_gcp",
    "obtener_nodo_demorado",
    "obtener_nodo_error",
    "obtener_todos_los_estados",

    # Exceptions
    "TritonError",
    "ProviderTimeoutError",
    "CorruptedPayloadError",
    "NetworkPeeringError",

    # Sanitizer
    "validate_timeout",
    "validate_cluster",

    # Storage
    "start_logging",
    "stop_logging",
    "get_logger",
]