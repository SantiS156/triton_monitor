

import argparse
import asyncio
import logging
import logging.config

import httpx

from triton_telemetry import core, sanitizer, storage
from triton_telemetry.exceptions import (
    CorruptedPayloadError,
    NetworkPeeringError,
    ProviderTimeoutError,
)

# Nombre de logger propio del operador CLI, separado del logger
LOGGER_OPERADOR = "app_operator"


#  Punto de Entrada CLI
def construir_parser() -> argparse.ArgumentParser:
    """Arma el parser de argumentos del operador CLI."""
    parser = argparse.ArgumentParser(
        prog="app_operator",
        description="Operador CLI del Sistema de Telemetría Multicloud Tritón",
    )

    # Restricción de dominio
    parser.add_argument(
        "--mode",
        choices=["nominal", "debug", "emergency"],
        default="nominal",
        help=(
            "Modo operativo: 'nominal' solo consulta proveedores reales, "
            "'debug' agrega nodos que fuerzan timeout/payload corrupto, "
            "'emergency' agrega además un nodo sin resolución DNS."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=sanitizer.validate_timeout,
        default=5.0,
        help="Timeout de red en segundos (0.1 a 5.0).",
    )

    parser.add_argument(
        "--cluster",
        type=sanitizer.validate_cluster,
        required=True,
        help="Identificador de cluster, formato cluster-<region>-<numero>, "
             "ej: cluster-aws-east-1",
    )

    grupo_salida = parser.add_mutually_exclusive_group()
    grupo_salida.add_argument(
        "--quiet", action="store_true", help="Salida por consola mínima (solo errores)."
    )
    grupo_salida.add_argument(
        "--verbose", action="store_true", help="Salida por consola detallada (nivel DEBUG)."
    )

    return parser


# Configuración declarativa de logging con dictConfig
def configurar_logging(args: argparse.Namespace) -> None:
    
    if args.quiet:
        nivel_consola = "ERROR"
    elif args.verbose:
        nivel_consola = "DEBUG"
    else:
        nivel_consola = "INFO"

    esquema_logging = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "estandar": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "consola": {
                "class": "logging.StreamHandler",
                "formatter": "estandar",
                "level": nivel_consola,
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            LOGGER_OPERADOR: {
                "handlers": ["consola"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(esquema_logging)


# Nodo de demostración para NetworkPeeringError
async def obtener_nodo_offline(cliente: httpx.AsyncClient) -> dict:
    try:
        respuesta = await cliente.get("https://nodo-inexistente.triton-invalido")
        respuesta.raise_for_status()
        return {"provider": "OfflineNode", "data": respuesta.json()}
    except httpx.ConnectError as error_original:
        error_propio = NetworkPeeringError(
            "No se pudo resolver el host o no hay conexión a internet"
        )
        error_propio.add_note("Fallo catastrófico de DNS/peering detectado")
        raise error_propio from error_original


# Orquestación async
async def ejecutar_diagnostico(args: argparse.Namespace) -> list:
    tareas_objetivo = [
        core.obtener_estado_aws,
        core.obtener_estado_azure,
        core.obtener_estado_gcp,
    ]

    if args.mode in ("debug", "emergency"):
        tareas_objetivo += [core.obtener_nodo_demorado, core.obtener_nodo_error]

    if args.mode == "emergency":
        tareas_objetivo.append(obtener_nodo_offline)

    async with httpx.AsyncClient(timeout=args.timeout) as cliente:
        async with asyncio.TaskGroup() as grupo_tareas:
            tareas = [grupo_tareas.create_task(fn(cliente)) for fn in tareas_objetivo]

    return [tarea.result() for tarea in tareas]


def mostrar_resultados(resultados: list) -> None:
    print("\n--- Diagnóstico completo, todos los nodos respondieron ---")
    for resultado in resultados:
        print(f"  · {resultado['provider']}: OK")


# Try principal (except*) + finally
def main() -> None:
    args = construir_parser().parse_args()
    configurar_logging(args)

    logger_operador = logging.getLogger(LOGGER_OPERADOR)
    logger_operador.info("Iniciando Tritón en modo '%s' sobre %s", args.mode, args.cluster)

    storage.start_logging()  # arranca el QueueListener del Integrante 4

    try:
        resultados = asyncio.run(ejecutar_diagnostico(args))

    except* ProviderTimeoutError as grupo:
        for excepcion in grupo.exceptions:
            logger_operador.error("Timeout de proveedor: %s", excepcion)
            for nota in getattr(excepcion, "__notes__", ()):
                print(f"  [FORENSE-TIMEOUT] {nota}")

    except* CorruptedPayloadError as grupo:
        # Se mitiga de forma lógica: se registra y el programa sigue su curso.
        for excepcion in grupo.exceptions:
            logger_operador.warning(
                "Payload corrupto mitigado, continuando ejecución: %s", excepcion
            )

    except* NetworkPeeringError as grupo:
        for excepcion in grupo.exceptions:
            logger_operador.critical("Fallo catastrófico de red/DNS: %s", excepcion)
            for nota in getattr(excepcion, "__notes__", ()):
                print(f"  [FORENSE-DNS] {nota}")

    else:
        mostrar_resultados(resultados)

    finally:
        # solo apagado ordenado del listener de hilos
        logger_operador.info("Apagando listener de logging en segundo plano")
        storage.stop_logging()


if __name__ == "__main__":
    main()
