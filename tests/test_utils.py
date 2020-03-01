from tempfile import NamedTemporaryFile

import pytest


@pytest.fixture
def temp_file():

    # TESTDIR for temporary files usually defaults to "/tmp",
    # which may not have XATTR support (e.g. tmpfs);
    # manual override here.
    TESTDIR = None
    tempfile = NamedTemporaryFile(dir=TESTDIR)
    tempfilename = tempfile.name
    yield tempfilename
    tempfile.close()


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


def test_backup_files(temp_file):
    import pathlib
    import osxmetadata
    from osxmetadata.utils import load_backup_file, write_backup_file

    meta = osxmetadata.OSXMetaData(temp_file)
    meta.comment = "Hello World!"
    meta.keywords = ["foo", "bar"]

    filename = pathlib.Path(temp_file).name

    backup_data = {}
    backup_data[filename] = meta._to_dict()

    TESTDIR = None
    backup_file = NamedTemporaryFile(dir=TESTDIR)

    write_backup_file(backup_file.name, backup_data)
    backup_data2 = load_backup_file(backup_file.name)

    assert backup_data2[filename]["com.apple.metadata:kMDItemKeywords"] == [
        "foo",
        "bar",
    ]
    assert backup_data2[filename]["com.apple.metadata:kMDItemComment"] == "Hello World!"

