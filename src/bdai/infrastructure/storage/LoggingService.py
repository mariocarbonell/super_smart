import logging
import traceback


def log_info(text: str) -> None:
    logging.info(text)
    print(text)


def log_trace(text: str) -> None:
    logging.info(text)


def log_console(text: str, first=False) -> None:
    if not first:
        print('\r', end="")
    print(text, end="")


def log_error(text: str = '') -> None:
    logging.error(traceback.format_exc())
    logging.error(text)
