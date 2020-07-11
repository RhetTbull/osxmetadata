#!/usr/bin/env python

from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
import platform


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


def test_download_where_from(temp_file):
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    expected = ["http://google.com", "https://apple.com"]
    meta.wherefroms = expected
    wf = meta.wherefroms
    assert sorted(wf) == sorted(expected)
    assert sorted(meta.get_attribute("wherefroms")) == sorted(expected)
