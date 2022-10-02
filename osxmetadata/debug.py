import logging

_DEBUG = False

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s",
)

if not _DEBUG:
    logging.disable(logging.DEBUG)


def _get_logger():
    """Used only for testing

    Returns:
        logging.Logger object -- logging.Logger object for osxmetadata
    """
    return logging.Logger(__name__)


def _set_debug(debug):
    """Enable or disable debug logging"""
    global _DEBUG
    _DEBUG = debug
    if debug:
        logging.disable(logging.NOTSET)
    else:
        logging.disable(logging.DEBUG)


def _debug():
    """returns True if debugging turned on (via _set_debug), otherwise, false"""
    return _DEBUG
