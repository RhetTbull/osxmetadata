#!/usr/bin/env python

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


def test_platform():
    # this module only works on Mac (darwin)
    import sys

    assert sys.platform == "darwin"


def test_tags(temp_file):
    #     # Not using setlocale(LC_ALL, ..) to set locale because
    #     # sys.getfilesystemencoding() implementation falls back
    #     # to user's preferred locale by calling setlocale(LC_ALL, '').
    #     xattr.compat.fs_encoding = 'UTF-8'

    from osxmetadata import OSXMetaData, _MAX_FINDERCOMMENT

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = ["Test", "Green"]
    meta.tags.update(*tagset)
    assert set(meta.tags) == set(tagset)

    # add tags
    meta.tags.add("Foo")
    assert set(meta.tags) != set(tagset)
    assert set(meta.tags) == set(["Test", "Green", "Foo"])

    # __iadd__
    meta.tags += "Bar"
    assert set(meta.tags) == set(["Test", "Green", "Foo", "Bar"])

    # __repr__
    tags = set(meta.tags)
    assert tags == set(["Test", "Green", "Foo", "Bar"])

    # remove tags
    meta.tags.remove("Test")
    assert set(meta.tags) == set(["Green", "Foo", "Bar"])

    # remove tag that doesn't exist, raises KeyError
    with pytest.raises(KeyError):
        assert meta.tags.remove("FooBar")

    # discard tags
    meta.tags.discard("Green")
    assert set(meta.tags) == set(["Foo", "Bar"])

    # discard tag that doesn't exist, no error
    meta.tags.discard("FooBar")
    assert set(meta.tags) == set(["Foo", "Bar"])

    # len
    assert len(meta.tags) == 2

    # clear tags
    meta.tags.clear()
    assert set(meta.tags) == set([])


def test_finder_comments(temp_file):
    from osxmetadata import OSXMetaData, _MAX_FINDERCOMMENT

    meta = OSXMetaData(temp_file)
    fc = "This is my new comment"
    meta.finder_comment = fc
    assert meta.finder_comment == fc
    meta.finder_comment += ", foo"
    fc += ", foo"
    assert meta.finder_comment == fc

    with pytest.raises(ValueError):
        meta.finder_comment = "x" * _MAX_FINDERCOMMENT + "x"

    # set finder comment to None same as ''
    meta.finder_comment = None
    assert meta.finder_comment == ""

    meta.finder_comment = ""
    assert meta.finder_comment == ""


def test_name(temp_file):
    from osxmetadata import OSXMetaData
    import pathlib

    meta = OSXMetaData(temp_file)
    fname = pathlib.Path(temp_file)
    assert meta.name == fname.resolve().as_posix()


def test_download_date(temp_file):
    from osxmetadata import OSXMetaData
    import datetime

    meta = OSXMetaData(temp_file)
    dt = datetime.datetime.now()
    meta.download_date = dt
    assert meta.download_date == dt


def test_download_where_from(temp_file):
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    meta.where_from = ["http://google.com", "https://apple.com"]
    wf = meta.where_from
    assert wf == ["http://google.com", "https://apple.com"]


def test_file_not_exists(temp_file):
    from osxmetadata import OSXMetaData

    with pytest.raises(Exception):
        # kludge to create a file that almost certainly doesn't exist
        # TODO: make this less kludgy
        bad_filename = str(temp_file + temp_file)
        _ = OSXMetaData(bad_filename)
