class TritonError(Exception):
    """Excepción base para los errores del sistema Tritón."""

class ProviderTimeoutError(TritonError):
    """Indica que un proveedor superó el tiempo de espera."""

class CorruptedPayloadError(TritonError):
    """Indica una respuesta HTTP corrupta o inesperada."""

class NetworkPeeringError(TritonError):
    """Indica un fallo de red o resolución de hosts."""

