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
    meta.tags += ["Bar"]
    assert set(meta.tags) == set(["Test", "Green", "Foo", "Bar"])

    # __iadd__ set
    meta.tags += set(["Baz"])
    assert set(meta.tags) == set(["Test", "Green", "Foo", "Bar", "Baz"])

    # __repr__
    tags = set(meta.tags)
    assert tags == set(["Test", "Green", "Foo", "Bar", "Baz"])

    # remove tags
    meta.tags.remove("Test")
    assert set(meta.tags) == set(["Green", "Foo", "Bar", "Baz"])

    # remove tag that doesn't exist, raises KeyError
    with pytest.raises(KeyError):
        assert meta.tags.remove("FooBar")

    # discard tags
    meta.tags.discard("Green")
    assert set(meta.tags) == set(["Foo", "Bar", "Baz"])

    # discard tag that doesn't exist, no error
    meta.tags.discard("FooBar")
    assert set(meta.tags) == set(["Foo", "Bar", "Baz"])

    # len
    assert len(meta.tags) == 3

    # clear tags
    meta.tags.clear()
    assert set(meta.tags) == set([])


def test_tags_2(temp_file):
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

    # __iadd__ string
    meta.tags += "Bar"
    assert set(meta.tags) == set(["Test", "Green", "B", "a", "r"])

    # len
    assert len(meta.tags) == 5

    # clear tags
    meta.tags.clear()
    assert set(meta.tags) == set([])


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
    assert meta.findercomment == None

    # can we set findercomment after is was set to None?
    meta.findercomment = "bar"
    assert meta.findercomment == "bar"


def test_creator(temp_file):
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    creator = "Rhet Turnbull"
    meta.creator = creator
    assert meta.creator == creator

    creator += " and you!"
    meta.creator = creator
    assert meta.creator == creator

    meta.creator = None
    assert meta.creator is None


@pytest.mark.skipif(
    int(platform.mac_ver()[0].split(".")[1]) >= 15,
    reason="limit on finder comment length seems to be gone on 10.15+",
)
def test_finder_comments_max(temp_file):
    from osxmetadata import OSXMetaData, _MAX_FINDERCOMMENT

    meta = OSXMetaData(temp_file)
    with pytest.raises(ValueError):
        meta.findercomment = "x" * _MAX_FINDERCOMMENT + "x"


def test_name(temp_file):
    from osxmetadata import OSXMetaData
    import pathlib

    meta = OSXMetaData(temp_file)
    fname = pathlib.Path(temp_file)
    assert meta.name == fname.resolve().as_posix()


def test_downloaded_date(temp_file):
    from osxmetadata import OSXMetaData
    import datetime

    meta = OSXMetaData(temp_file)
    dt = datetime.datetime.now()
    meta.downloadeddate = dt
    assert meta.downloadeddate == [dt]


def test_downloaded_date_isoformat(temp_file):
    from osxmetadata import OSXMetaData
    import datetime

    meta = OSXMetaData(temp_file)
    dt = "2020-02-17 00:25:00"
    meta.downloadeddate = dt
    assert meta.downloadeddate == [datetime.datetime.fromisoformat(dt)]


def test_download_where_froms(temp_file):
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    meta.wherefroms = ["http://google.com", "https://apple.com"]
    wf = meta.wherefroms
    assert sorted(wf) == sorted(["http://google.com", "https://apple.com"])


def test_file_not_exists(temp_file):
    from osxmetadata import OSXMetaData

    with pytest.raises(Exception):
        # kludge to create a file that almost certainly doesn't exist
        # TODO: make this less kludgy
        bad_filename = str(temp_file + temp_file)
        _ = OSXMetaData(bad_filename)
