import logging

from actyon.__meta__ import PACKAGE_NAME


def get_logger(name: str = PACKAGE_NAME) -> logging.Logger:
    log: logging.Logger = logging.getLogger(name)
    if len(log.handlers) == 0:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.StreamHandler()
        handler.formatter = formatter
        log.addHandler(handler)
    return log
