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


def test_finder_comments(temp_file):
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    fc = "This is my new comment"
    meta.findercomment = fc
    assert meta.findercomment == fc
    meta.findercomment += ", foo"
    fc += ", foo"
    assert meta.findercomment == fc

    # set finder comment to "" results in null string but not deleted
    meta.findercomment = ""
    assert meta.findercomment == ""

    meta.findercomment = "foo"
    assert meta.findercomment == "foo"

    # set finder comment to None deletes it
    meta.findercomment = None
    assert meta.findercomment is None

    # can we set findercomment after is was set to None?
    meta.findercomment = "bar"
    assert meta.findercomment == "bar"


def test_finder_comments_2(temp_file):
    """ test get/set attribute """

    from osxmetadata import OSXMetaData
    from osxmetadata.constants import kMDItemFinderComment

    attribute = kMDItemFinderComment

    meta = OSXMetaData(temp_file)
    fc = "This is my new comment"
    meta.set_attribute(attribute, fc)
    assert meta.findercomment == fc
    meta.findercomment += ", foo"
    fc += ", foo"
    assert meta.findercomment == fc

    # set finder comment to "" results in null string but not deleted
    meta.set_attribute(attribute, "")
    assert meta.get_attribute(attribute) == ""

    meta.set_attribute(attribute, "foo")
    assert meta.get_attribute(attribute) == "foo"

    # set finder comment to None deletes it
    meta.set_attribute(attribute, "")
    assert meta.get_attribute(attribute) == ""

    meta.clear_attribute(attribute)
    assert meta.get_attribute(attribute) is None

    # can we set findercomment after is was set to None?
    meta.set_attribute(attribute, "bar")
    assert meta.get_attribute(attribute) == "bar"


def test_finder_comments_dir():
    """ test get/set attribute but on a directory, not on a file"""

    from osxmetadata import OSXMetaData
    from osxmetadata.constants import kMDItemFinderComment

    with TemporaryDirectory() as temp_dir:
        attribute = kMDItemFinderComment

        meta = OSXMetaData(temp_dir)
        fc = "This is my new comment"
        meta.set_attribute(attribute, fc)
        assert meta.findercomment == fc
        meta.findercomment += ", foo"
        fc += ", foo"
        assert meta.findercomment == fc


# @pytest.mark.skipif(
#     int(platform.mac_ver()[0].split(".")[1]) >= 15,
#     reason="limit on finder comment length seems to be gone on 10.15+",
# )
# def test_finder_comments_max(temp_file):
#     from osxmetadata import OSXMetaData, _MAX_FINDERCOMMENT

#     meta = OSXMetaData(temp_file)
#     with pytest.raises(ValueError):
#         meta.findercomment = "x" * _MAX_FINDERCOMMENT + "x"
