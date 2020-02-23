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


def test_download_where_from(temp_file):
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    expected = ["http://google.com", "https://apple.com"]
    meta.wherefroms = expected
    wf = meta.wherefroms
    assert sorted(wf) == sorted(expected)
    assert sorted(meta.get_attribute("wherefroms")) == sorted(expected)
