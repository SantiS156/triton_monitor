import gzip
import logging
import logging.handlers
import os
import queue
import shutil

from.logging_engine import UTCJSONFormatter


LOG_FILE = "application.log"
MAX_BYTES = 2 * 1024 * 1024  # 2 MB
BACKUP_COUNT = 3

# Cola segura para hilos
log_queue = queue.Queue()

def gzip_namer(filename: str) -> str:
    return filename + ".gz"

def gzip_rotator(source: str, destination: str) -> None:
    temporary_file = destination + ".tmp"

    try:
        with open(source, "rb") as source_file:
            with gzip.open(temporary_file, "wb") as gzip_file:
                shutil.copyfileobj(source_file, gzip_file)

        os.replace(temporary_file, destination)
        os.remove(source)

    except Exception:
        if os.path.exists(temporary_file):
            try:
                os.remove(temporary_file)
            except OSError:
                pass

        raise

# Manejador rotativo
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE,
    maxBytes=MAX_BYTES,
    backupCount=BACKUP_COUNT,
    encoding="utf-8"
)

file_handler.namer = gzip_namer
file_handler.rotator = gzip_rotator
file_handler.setFormatter(UTCJSONFormatter())


# QueueHandler: envía los logs a la cola
queue_handler = logging.handlers.QueueHandler(log_queue)

# QueueListener: procesa la cola en un hilo separado
queue_listener = logging.handlers.QueueListener(
    log_queue,
    file_handler,
    respect_handler_level=True
)

# Logger principal
logger = logging.getLogger("application")
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(queue_handler)
logger.propagate = False

def start_logging() -> None:
    if queue_listener._thread is None or not queue_listener._thread.is_alive():
        queue_listener.start()

def stop_logging() -> None:
    if queue_listener._thread is not None and queue_listener._thread.is_alive():
        queue_listener.stop()

def get_logger() -> logging.Logger:
    return logger
