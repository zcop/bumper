import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import MutableMapping, Union

logformat = logging.Formatter(
    "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(module)s :: %(funcName)s :: %(lineno)d :: %(message)s"
)

__loggers: MutableMapping[str, logging.Logger] = {}
log_to_stdout = os.environ.get("LOG_TO_STDOUT")


def get_logger(name: str, rotate: RotatingFileHandler = None) -> logging.Logger:
    found_logger = __loggers.get(name)
    if found_logger:
        return found_logger

    logger = logging.getLogger(name)

    if not log_to_stdout:
        if not rotate:
            rotate = RotatingFileHandler(
                f"logs/{name}.log", maxBytes=5000000, backupCount=5
            )
            rotate.setFormatter(logformat)
        logger.addHandler(rotate)
    else:
        logger.addHandler(logging.StreamHandler(sys.stdout))

    __loggers[name] = logger

    if name == "mqttserver":
        get_logger("transitions", rotate).setLevel(
            logging.CRITICAL + 1
        )  # Ignore this logger
        get_logger("passlib", rotate).setLevel(
            logging.CRITICAL + 1
        )  # Ignore this logger
        get_logger("amqtt.broker", rotate)
        get_logger("amqtt.mqtt.protocol", rotate)
        get_logger("amqtt.client", rotate)

    return logger


def convert_to_millis(seconds: Union[int, float]) -> int:
    """Convert seconds to milliseconds."""
    return int(round(seconds * 1000))


def get_current_time_as_millis() -> int:
    return convert_to_millis(datetime.utcnow().timestamp())
