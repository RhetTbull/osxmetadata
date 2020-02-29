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

    from osxmetadata import OSXMetaData

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = ["Test", "Green"]
    meta.tags.extend(tagset)
    assert meta.tags == tagset

    # extend with string
    meta.tags.extend("Foo")
    assert meta.tags == ["Test", "Green", "F", "o", "o"]

    # add tags
    meta.tags.append("Hello")
    assert meta.tags != tagset
    assert meta.tags == ["Test", "Green", "F", "o", "o", "Hello"]

    # __iadd__
    meta.tags += ["Bar"]
    assert meta.tags == ["Test", "Green", "F", "o", "o", "Hello", "Bar"]

    # __repr__
    # TODO

    # remove tags
    meta.tags.remove("Test")
    assert meta.tags == ["Green", "F", "o", "o", "Hello", "Bar"]

    # remove tag that doesn't exist, raises KeyError
    with pytest.raises(ValueError):
        assert meta.tags.remove("FooBar")

    # len
    assert len(meta.tags) == 6

    # clear tags
    meta.tags.clear()
    assert meta.tags == []


def test_tags_2(temp_file):

    from osxmetadata import OSXMetaData

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = ["Test", "Green"]
    meta.tags = tagset
    assert meta.tags == tagset

    assert "Test" in meta.tags
    assert "Foo" not in meta.tags

    meta.tags.remove("Test")
    assert "Test" not in meta.tags


def test_tags_3(temp_file):

    from osxmetadata import OSXMetaData
    from osxmetadata.constants import kMDItemUserTags

    attribute = kMDItemUserTags

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = ["Test", "Green"]

    meta.set_attribute(attribute, tagset)
    tags = meta.get_attribute(attribute)
    assert tags == tagset

    meta.update_attribute(attribute, ["Foo"])
    tags = meta.get_attribute(attribute)
    assert tags == ["Test", "Green", "Foo"]

    meta.remove_attribute(attribute, "Foo")
    tags = meta.get_attribute(attribute)
    assert tags == ["Test", "Green"]

    meta.update_attribute(attribute, {"Foo"})
    tags = meta.get_attribute(attribute)
    assert tags == ["Test", "Green", "Foo"]

    meta.clear_attribute(attribute)
    tags = meta.get_attribute(attribute)
    assert len(tags) == 0


def test_tags_clear(temp_file):

    from osxmetadata import OSXMetaData
    from osxmetadata.constants import kMDItemUserTags

    attribute = kMDItemUserTags

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = ["Test", "Green"]

    meta.set_attribute(attribute, tagset)
    tags = meta.get_attribute(attribute)
    assert tags == tagset

    meta.clear_attribute(attribute)
    tags = meta.get_attribute(attribute)
    assert tags == []


def test_tags_assign(temp_file):
    """ test assigning one tag object to another """
    from osxmetadata import OSXMetaData

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = ["Test", "Green"]
    meta.tags = tagset
    assert meta.tags == tagset

    # create second temp file
    TESTDIR = None
    tempfile2 = NamedTemporaryFile(dir=TESTDIR)
    temp_file_2 = tempfile2.name

    meta2 = OSXMetaData(temp_file_2)
    tagset2 = ["test2", "Blue"]
    meta2.tags = tagset2
    assert meta2.tags == tagset2

    meta.tags = meta2.tags
    assert meta.tags == tagset2

    # close second tempfile, first gets closed automatically
    tempfile2.close()


def test_tags_4(temp_file):
    """ Test various list methods """
    from osxmetadata import OSXMetaData
    from osxmetadata.constants import _kMDItemUserTags

    attribute = _kMDItemUserTags

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = ["Test", "Green", "Foo"]

    meta.tags = tagset
    assert meta.tags == tagset
    assert meta.get_attribute(attribute) == tagset

    idx = meta.tags.index("Green")
    assert idx == 1

    count = meta.tags.count("Test")
    assert count == 1

    count = meta.tags.count("Bar")
    assert count == 0

    meta.tags.sort()
    assert meta.tags == ["Foo", "Green", "Test"]
    assert meta.get_attribute(attribute) == ["Foo", "Green", "Test"]

    meta.tags.sort(reverse=True)
    assert meta.tags == ["Test", "Green", "Foo"]
    assert meta.get_attribute(attribute) == ["Test", "Green", "Foo"]

    # sort by key
    meta.tags.sort(key=lambda tag: len(tag))
    assert meta.tags == ["Foo", "Test", "Green"]
    assert meta.get_attribute(attribute) == ["Foo", "Test", "Green"]

    meta.tags.reverse()
    assert meta.tags == ["Green", "Test", "Foo"]
    assert meta.get_attribute(attribute) == ["Green", "Test", "Foo"]

    tag_expected = "Test"
    tag_got = meta.tags.pop(1)
    assert tag_got == tag_expected
    assert meta.tags == ["Green", "Foo"]
    assert meta.get_attribute(attribute) == ["Green", "Foo"]

