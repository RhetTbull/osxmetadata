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


def test_download_date(temp_file):
    from osxmetadata import OSXMetaData
    import datetime

    meta = OSXMetaData(temp_file)
    dt = datetime.datetime.now()
    meta.downloadeddate = dt
    assert meta.downloadeddate == [dt]
    assert meta.get_attribute("downloadeddate") == [dt]
