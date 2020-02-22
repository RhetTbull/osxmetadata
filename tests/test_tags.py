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


def test_tags(temp_file):

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


def test_tags_3(temp_file):

    from osxmetadata import OSXMetaData
    from osxmetadata.attributes import ATTRIBUTES

    attribute = ATTRIBUTES["tags"]

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = {"Test", "Green"}

    meta.set_attribute(attribute, tagset)
    tags = meta.get_attribute(attribute)
    assert sorted(tags) == sorted(tagset)

    meta.update_attribute(attribute, ["Foo"])
    tags = meta.get_attribute(attribute)
    assert sorted(tags) == sorted({"Test", "Green", "Foo"})

    meta.remove_attribute(attribute, "Foo")
    tags = meta.get_attribute(attribute)
    assert sorted(tags) == sorted({"Test", "Green"})

    meta.update_attribute(attribute, {"Foo"})
    tags = meta.get_attribute(attribute)
    assert sorted(tags) == sorted({"Test", "Green", "Foo"})

    meta.clear_attribute

