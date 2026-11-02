import logging

from valveexe.exe import (ValveExe, GameNotRunning,
                          EXEC, RCON, AUTO, CONSOLES)
from valveexe.logger import Logger
from valveexe.console import VConsole, RconConsole, ExecConsole

# Silent by default: a library shouldn't emit output unless the app asks for it.
logging.getLogger(__name__).addHandler(logging.NullHandler())


def enable_debug(level=logging.DEBUG):
    '''Turn on verbose ValveEXE debug logging to stderr.

    Call this to see what ValveEXE is doing internally (process hijacking,
    rcon eligibility checks, console selection, etc.). Idempotent.

    :param level: The logging level to enable (default ``logging.DEBUG``).
    :type level: int
    '''
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '[%(levelname)s] %(name)s: %(message)s'))
        logger.addHandler(handler)
