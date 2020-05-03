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

    from osxmetadata import OSXMetaData, Tag

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = [Tag("Test"), Tag("Green")]
    meta.tags.extend(tagset)
    assert meta.tags == tagset

    # extend
    meta.tags.extend([Tag("Foo")])
    assert meta.tags == [Tag("Test"), Tag("Green"), Tag("Foo")]

    # add tags
    meta.tags.append(Tag("Hello"))
    assert meta.tags != tagset
    assert meta.tags == [Tag("Test"), Tag("Green"), Tag("Foo"), Tag("Hello")]

    # __iadd__
    meta.tags += [Tag("Bar")]
    assert meta.tags == [
        Tag("Test"),
        Tag("Green"),
        Tag("Foo"),
        Tag("Hello"),
        Tag("Bar"),
    ]

    # __repr__
    # TODO

    # remove tags
    meta.tags.remove(Tag("Test"))
    assert meta.tags == [Tag("Green"), Tag("Foo"), Tag("Hello"), Tag("Bar")]

    # remove tag that doesn't exist, raises KeyError
    with pytest.raises(ValueError):
        assert meta.tags.remove(Tag("FooBar"))

    # len
    assert len(meta.tags) == 4

    # clear tags
    meta.tags.clear()
    assert meta.tags == []


def test_tags_2(temp_file):

    from osxmetadata import OSXMetaData, Tag

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = [Tag("Test"), Tag("Green")]
    meta.tags = tagset
    assert meta.tags == tagset

    assert Tag("Test") in meta.tags
    assert Tag("Foo") not in meta.tags

    meta.tags.remove(Tag("Test"))
    assert Tag("Test") not in meta.tags


def test_tags_3(temp_file):

    from osxmetadata import OSXMetaData, Tag
    from osxmetadata.constants import kMDItemUserTags

    attribute = kMDItemUserTags

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = [Tag("Test"), Tag("Green")]

    meta.set_attribute(attribute, tagset)
    tags = meta.get_attribute(attribute)
    assert tags == tagset

    meta.update_attribute(attribute, [Tag("Foo")])
    tags = meta.get_attribute(attribute)
    assert tags == [Tag("Test"), Tag("Green"), Tag("Foo")]

    meta.remove_attribute(attribute, Tag("Foo"))
    tags = meta.get_attribute(attribute)
    assert tags == [Tag("Test"), Tag("Green")]

    meta.update_attribute(attribute, [Tag("Foo")])
    tags = meta.get_attribute(attribute)
    assert tags == [Tag("Test"), Tag("Green"), Tag("Foo")]

    meta.clear_attribute(attribute)
    tags = meta.get_attribute(attribute)
    assert len(tags) == 0


def test_tags_exception(temp_file):

    from osxmetadata import OSXMetaData, Tag

    # update tags
    meta = OSXMetaData(temp_file)
    with pytest.raises(TypeError):
        meta.tags = ["Foo"]

    with pytest.raises(TypeError):
        meta.tags = "Foo"


def test_tags_clear(temp_file):

    from osxmetadata import OSXMetaData, Tag
    from osxmetadata.constants import kMDItemUserTags

    attribute = kMDItemUserTags

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = [Tag("Test"), Tag("Green")]

    meta.set_attribute(attribute, tagset)
    tags = meta.get_attribute(attribute)
    assert tags == tagset

    meta.clear_attribute(attribute)
    tags = meta.get_attribute(attribute)
    assert tags == []


def test_tags_assign(temp_file):
    """ test assigning one tag object to another """
    from osxmetadata import OSXMetaData, Tag

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = [Tag("Test"), Tag("Green")]
    meta.tags = tagset
    assert meta.tags == tagset

    # create second temp file
    TESTDIR = None
    tempfile2 = NamedTemporaryFile(dir=TESTDIR)
    temp_file_2 = tempfile2.name

    meta2 = OSXMetaData(temp_file_2)
    tagset2 = [Tag("test2"), Tag("Blue")]
    meta2.tags = tagset2
    assert meta2.tags == tagset2

    meta.tags = meta2.tags
    assert meta.tags == tagset2

    # close second tempfile, first gets closed automatically
    tempfile2.close()


def test_tags_4(temp_file):
    """ Test various list methods """
    from osxmetadata import OSXMetaData, Tag
    from osxmetadata.constants import _kMDItemUserTags

    attribute = _kMDItemUserTags

    # update tags
    meta = OSXMetaData(temp_file)
    tagset = [Tag("Test"), Tag("Green"), Tag("Foo")]

    meta.tags = tagset
    assert meta.tags == tagset
    assert meta.get_attribute(attribute) == tagset

    idx = meta.tags.index(Tag("Green"))
    assert idx == 1

    count = meta.tags.count(Tag("Test"))
    assert count == 1

    count = meta.tags.count(Tag("Bar"))
    assert count == 0

    meta.tags.sort()
    assert meta.tags == [Tag("Foo"), Tag("Green"), Tag("Test")]
    assert meta.get_attribute(attribute) == [Tag("Foo"), Tag("Green"), Tag("Test")]

    meta.tags.sort(reverse=True)
    assert meta.tags == [Tag("Test"), Tag("Green"), Tag("Foo")]
    assert meta.get_attribute(attribute) == [Tag("Test"), Tag("Green"), Tag("Foo")]

    # sort by key
    meta.tags.sort(key=lambda tag: len(tag))
    assert meta.tags == [Tag("Foo"), Tag("Test"), Tag("Green")]
    assert meta.get_attribute(attribute) == [Tag("Foo"), Tag("Test"), Tag("Green")]

    # todo: reverse not working
    # meta.tags.reverse()
    # assert meta.tags == [Tag("Green"), Tag("Test"), Tag("Foo")]
    # assert meta.get_attribute(attribute) == [Tag("Green"), Tag("Test"), Tag("Foo")]

    # tag_expected = Tag("Test")
    # tag_got = meta.tags.pop(1)
    # assert tag_got == tag_expected
    # assert meta.tags == [Tag("Green"), Tag("Foo")]
    # assert meta.get_attribute(attribute) == [Tag("Green"), Tag("Foo")]

    tag_expected = Tag("Test")
    tag_got = meta.tags.pop(1)
    assert tag_got == tag_expected
    assert meta.tags == [Tag("Foo"), Tag("Green")]
    assert meta.get_attribute(attribute) == [Tag("Foo"), Tag("Green")]


def test_tag_factory():
    from osxmetadata import Tag, FINDER_COLOR_BLUE, FINDER_COLOR_GREEN
    from osxmetadata.findertags import tag_factory

    tag_ = tag_factory("Foo")
    assert isinstance(tag_, Tag)
    assert tag_ == Tag("Foo")

    tag_ = tag_factory("Foo,Blue")
    assert isinstance(tag_, Tag)
    assert tag_ == Tag("Foo", FINDER_COLOR_BLUE)

    tag_ = tag_factory("Foo,blue")
    assert isinstance(tag_, Tag)
    assert tag_ == Tag("Foo", FINDER_COLOR_BLUE)

    tag_ = tag_factory(f"Foo,{FINDER_COLOR_BLUE}")
    assert isinstance(tag_, Tag)
    assert tag_ == Tag("Foo", FINDER_COLOR_BLUE)

    tag_ = tag_factory("green")
    assert isinstance(tag_, Tag)
    assert tag_ == Tag("Green", FINDER_COLOR_GREEN)
