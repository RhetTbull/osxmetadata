from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest


@pytest.fixture(params=["file", "dir"])
def temp_file(request):

    # TESTDIR for temporary files usually defaults to "/tmp",
    # which may not have XATTR support (e.g. tmpfs);
    # manual override here.
    TESTDIR = None
    if request.param == "file":
        tempfile = NamedTemporaryFile(dir=TESTDIR)
        tempfilename = tempfile.name
        yield tempfilename
        tempfile.close()
    else:
        tempdir = TemporaryDirectory(dir=TESTDIR)
        tempdirname = tempdir.name
        yield tempdirname
        tempdir.cleanup()


def test_debug_enable():
    import osxmetadata
    import logging

    osxmetadata._set_debug(True)
    logger = osxmetadata.debug._get_logger()
    assert logger.isEnabledFor(logging.DEBUG)


def test_debug_disable():
    import osxmetadata
    import logging

    osxmetadata._set_debug(False)
    logger = osxmetadata.debug._get_logger()
    assert not logger.isEnabledFor(logging.DEBUG)


def test_backup_files(temp_file):
    import pathlib
    import osxmetadata
    from osxmetadata.backup import load_backup_file, write_backup_file

    meta = osxmetadata.OSXMetaData(temp_file)
    meta.comment = "Hello World!"
    meta.keywords = ["foo", "bar"]

    filename = pathlib.Path(temp_file).name

    backup_data = {filename: meta.asdict()}
    
    TESTDIR = None
    backup_file = NamedTemporaryFile(dir=TESTDIR)

    write_backup_file(backup_file.name, backup_data)
    backup_data2 = load_backup_file(backup_file.name)

    assert backup_data2[filename]["com.apple.metadata:kMDItemKeywords"] == [
        "foo",
        "bar",
    ]
    assert backup_data2[filename]["com.apple.metadata:kMDItemComment"] == "Hello World!"
