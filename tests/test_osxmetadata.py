#!/usr/bin/env python

from tempfile import NamedTemporaryFile

import pytest
import platform


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


def test_platform():
    # this module only works on Mac (darwin)
    import sys

    assert sys.platform == "darwin"


def test_name(temp_file):
    from osxmetadata import OSXMetaData
    import pathlib

    meta = OSXMetaData(temp_file)
    fname = pathlib.Path(temp_file)
    assert meta.name == fname.resolve().as_posix()


def test_file_not_exists(temp_file):
    from osxmetadata import OSXMetaData

    with pytest.raises(Exception):
        # kludge to create a file that almost certainly doesn't exist
        # TODO: make this less kludgy
        bad_filename = str(temp_file + temp_file)
        _ = OSXMetaData(bad_filename)
