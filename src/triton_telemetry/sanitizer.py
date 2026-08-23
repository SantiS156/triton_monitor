import argparse
import re 

CLUSTER_PATTERN = re.compile(
    r"^cluster-[a-z]+-[a-z]+-\d+$"
)

def validate_timeout(value):
    """
    Valida el parámetro --timeout recibido desde la CLI.

    El valor debe ser numérico y estar dentro del rango
    permitido de 0.1 a 5.0 segundos.

    Args:
        value: Valor recibido desde la línea de comandos.

    Returns:
        float: Valor convertido a número decimal.

    Raises:
        argparse.ArgumentTypeError: Si el valor no es
            numérico o está fuera del rango permitido.
    """

    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "El timeout debe ser un número."
        ) from error

    if not 0.1 <= timeout <= 5.0:
        raise argparse.ArgumentTypeError(
            "El timeout debe estar entre 0.1 y 5.0 segundos."
        )
    
    return timeout


def validate_cluster(value):
    """
    Valida el identificador de cluster recibido desde la CLI.

    El valor debe respetar el formato:
    cluster-<region>-<numero>.

    Args:
        value: Identificador de cluster recibido desde
            la línea de comandos.

    Returns:
        str: Identificador de cluster validado.

    Raises:
        argparse.ArgumentTypeError: Si el identificador
            no cumple con el formato requerido.
    """
    
    if not CLUSTER_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "El cluster debe tener el formato cluster-<region>-<numero>."
        )

    return value 