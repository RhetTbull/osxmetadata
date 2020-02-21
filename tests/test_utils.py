import pytest


def test_debug_enable():
    import osxmetadata
    import logging

    osxmetadata._set_debug(True)
    logger = osxmetadata.utils._get_logger()
    assert logger.isEnabledFor(logging.DEBUG)


def test_debug_disable():
    import osxmetadata
    import logging

    osxmetadata._set_debug(False)
    logger = osxmetadata.utils._get_logger()
    assert not logger.isEnabledFor(logging.DEBUG)
