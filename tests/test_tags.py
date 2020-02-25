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
    meta.tags.update(tagset)
    assert set(meta.tags) == set(tagset)

    # update non-iterable
    with pytest.raises(TypeError):
        meta.tags.update(1,2,3)

    # update with string
    meta.tags.update("Foo")
    assert set(meta.tags) == {"Test","Green","F","o"}

    # add tags
    meta.tags.add("Hello")
    assert set(meta.tags) != set(tagset)
    assert set(meta.tags) == set(["Test", "F", "o", "Green", "Hello"])

    # __ior__ 
    meta.tags |= {"Bar"}
    assert set(meta.tags) == set(["Test", "Green", "F", "o", "Hello", "Bar"])

    # __ior__ set
    meta.tags |= set(["Baz"])
    assert set(meta.tags) == set(["Test", "Green", "F", "o", "Hello", "Bar", "Baz"])

    # __ior__ error
    with pytest.raises(TypeError):
        meta.tags |= ["FooBar"]

    # __repr__
    tags = set(meta.tags)
    assert tags == set(["Test", "Green", "F", "o", "Hello", "Bar", "Baz"])

    # remove tags
    meta.tags.remove("Test")
    assert set(meta.tags) == set(["Green", "F", "o", "Hello", "Bar", "Baz"])

    # remove tag that doesn't exist, raises KeyError
    with pytest.raises(KeyError):
        assert meta.tags.remove("FooBar")

    # discard tags
    meta.tags.discard("Green")
    assert set(meta.tags) == set(["F", "o", "Hello", "Bar", "Baz"])

    # discard tag that doesn't exist, no error
    meta.tags.discard("FooBar")
    assert set(meta.tags) == set(["F","o", "Hello", "Bar", "Baz"])

    # len
    assert len(meta.tags) == 5

    # clear tags
    meta.tags.clear()
    assert set(meta.tags) == set([])


def test_tags_2(temp_file):

    from osxmetadata import OSXMetaData, _MAX_FINDERCOMMENT

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = ["Test", "Green"]
    meta.tags.update(tagset)
    assert set(meta.tags) == set(tagset)

    # __ior__ string
    with pytest.raises(TypeError):
        meta.tags |= "Bar"
    assert set(meta.tags) == set(["Test", "Green"])

    # len
    assert len(meta.tags) == 2 

    # clear tags
    meta.tags.clear()
    assert set(meta.tags) == set([])


def test_tags_3(temp_file):

    from osxmetadata import OSXMetaData
    from osxmetadata.constants import kMDItemUserTags

    attribute = kMDItemUserTags

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

    # TODO: should clear_attribute cause get_attribute to return None?
    # it does for scalar attributes
    meta.clear_attribute(attribute)
    tags = meta.get_attribute(attribute)
    assert set(tags) == set([])


def test_tags_assign(temp_file):
    """ test assigning one tag object to another """
    from osxmetadata import OSXMetaData

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = {"Test", "Green"}
    meta.tags = tagset
    assert sorted(meta.tags) == sorted(tagset)

    # create second temp file
    TESTDIR = None
    tempfile2 = NamedTemporaryFile(dir=TESTDIR)
    temp_file_2 = tempfile2.name

    meta2 = OSXMetaData(temp_file_2)
    tagset2 = {"test2", "Blue"}
    meta2.tags = tagset2
    assert sorted(meta2.tags) == sorted(tagset2)

    meta.tags = meta2.tags
    assert sorted(meta.tags) == sorted(tagset2)

    # close second tempfile, first gets closed automatically
    tempfile2.close()
