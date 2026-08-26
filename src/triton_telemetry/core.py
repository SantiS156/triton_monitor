import asyncio
import httpx
from typing import Dict, Any, List

from .exceptions import ProviderTimeoutError, CorruptedPayloadError


async def obtener_estado_aws(cliente: httpx.AsyncClient) -> Dict[str, Any]:
    respuesta = await cliente.get("https://jsonplaceholder.typicode.com/posts/1")
    respuesta.raise_for_status()
    return {"provider": "AWS", "data": respuesta.json()}


async def obtener_estado_azure(cliente: httpx.AsyncClient) -> Dict[str, Any]:
    respuesta = await cliente.get("https://jsonplaceholder.typicode.com/posts/2")
    respuesta.raise_for_status()
    return {"provider": "Azure", "data": respuesta.json()}


async def obtener_estado_gcp(cliente: httpx.AsyncClient) -> Dict[str, Any]:
    respuesta = await cliente.get("https://jsonplaceholder.typicode.com/posts/3")
    respuesta.raise_for_status()
    return {"provider": "GCP", "data": respuesta.json()}


async def obtener_nodo_demorado(cliente: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        respuesta = await cliente.get("https://httpbin.org/delay/3")
        respuesta.raise_for_status()
        return {"provider": "DelayedNode", "data": respuesta.json()}
    except httpx.TimeoutException as excepcion_original:
        error_propio = ProviderTimeoutError("El proveedor tardó demasiado en responder")
        error_propio.add_note("Timeout superado en el nodo de telemetría de respaldo")
        raise error_propio from excepcion_original


async def obtener_nodo_error(cliente: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        respuesta = await cliente.get("https://httpbin.org/status/504")
        respuesta.raise_for_status()
        return {"provider": "ErrorNode", "data": respuesta.json()}
    except httpx.HTTPStatusError as error_nativo:
        raise CorruptedPayloadError("Estatus HTTP no esperado recibido") from error_nativo


async def obtener_todos_los_estados(segundos_limite: float = 5.0) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=segundos_limite) as cliente:
        async with asyncio.TaskGroup() as grupo_tareas:
            tarea_aws = grupo_tareas.create_task(obtener_estado_aws(cliente))
            tarea_azure = grupo_tareas.create_task(obtener_estado_azure(cliente))
            tarea_gcp = grupo_tareas.create_task(obtener_estado_gcp(cliente))

        return [
            tarea_aws.result(),
            tarea_azure.result(),
            tarea_gcp.result()
        ]