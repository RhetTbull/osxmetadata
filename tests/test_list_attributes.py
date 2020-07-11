#!/usr/bin/env python

from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
import platform

from osxmetadata.attributes import ATTRIBUTES
from osxmetadata.classes import _AttributeList


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


test_data = [
    (attr)
    for attr in sorted(list(ATTRIBUTES.keys()))
    if ATTRIBUTES[attr].class_ == _AttributeList and ATTRIBUTES[attr].type_ == str
]
ids = [
    attr
    for attr in sorted(list(ATTRIBUTES.keys()))
    if ATTRIBUTES[attr].class_ == _AttributeList and ATTRIBUTES[attr].type_ == str
]

test_data2 = [
    (attribute_name)
    for attribute_name in {
        ATTRIBUTES[attr].name
        for attr in sorted(ATTRIBUTES)
        if ATTRIBUTES[attr].class_ == _AttributeList and ATTRIBUTES[attr].type_ == str
    }
]
ids2 = [
    attribute_name
    for attribute_name in {
        ATTRIBUTES[attr].name
        for attr in sorted(ATTRIBUTES)
        if ATTRIBUTES[attr].class_ == _AttributeList and ATTRIBUTES[attr].type_ == str
    }
]


@pytest.mark.parametrize("attribute", test_data, ids=ids)
def test_list_attribute(temp_file, attribute):
    """ test set_attribute, get_attribute, etc for list items"""
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    expected = ["Foo"]
    meta.set_attribute(attribute, expected)
    got = meta.get_attribute(attribute)
    assert expected == got

    expected += ["Bar"]
    meta.append_attribute(attribute, ["Bar"])
    assert meta.get_attribute(attribute) == expected

    expected.remove("Bar")
    meta.remove_attribute(attribute, "Bar")
    assert meta.get_attribute(attribute) == expected

    with pytest.raises(ValueError):
        meta.remove_attribute(attribute, "Bar")

    expected += ["Flooz"]
    meta.update_attribute(attribute, ["Flooz"])
    assert meta.get_attribute(attribute) == expected

    meta.discard_attribute(attribute, "foo")
    assert meta.get_attribute(attribute) == expected

    meta.clear_attribute(attribute)
    assert meta.get_attribute(attribute) is None

    expected = ["Foo"]
    meta.set_attribute(attribute, expected)
    got = meta.get_attribute(attribute)
    assert expected == got


@pytest.mark.parametrize("attribute", test_data2, ids=ids2)
def test_list_attribute_2(temp_file, attribute):
    """ test getting and setting attribute by name """
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    setattr(meta, attribute, ["Foo", "Bar"])
    test_attr = getattr(meta, attribute)
    assert test_attr == ["Foo", "Bar"]
    assert meta.get_attribute(attribute) == ["Foo", "Bar"]


def test_list_methods(temp_file):
    """ Test various list methods """
    from osxmetadata import OSXMetaData
    from osxmetadata.constants import kMDItemKeywords

    attribute = kMDItemKeywords

    # updatekeywords
    meta = OSXMetaData(temp_file)
    keywordset = ["Test", "Green", "Foo"]

    meta.keywords = keywordset
    assert meta.keywords == keywordset
    assert meta.get_attribute(attribute) == keywordset

    idx = meta.keywords.index("Green")
    assert idx == 1

    count = meta.keywords.count("Test")
    assert count == 1

    count = meta.keywords.count("Bar")
    assert count == 0

    meta.keywords.sort()
    assert meta.keywords == ["Foo", "Green", "Test"]
    assert meta.get_attribute(attribute) == ["Foo", "Green", "Test"]

    meta.keywords.sort(reverse=True)
    assert meta.keywords == ["Test", "Green", "Foo"]
    assert meta.get_attribute(attribute) == ["Test", "Green", "Foo"]

    # sort by key
    meta.keywords.sort(key=lambda tag: len(tag))
    assert meta.keywords == ["Foo", "Test", "Green"]
    assert meta.get_attribute(attribute) == ["Foo", "Test", "Green"]

    meta.keywords.reverse()
    assert meta.keywords == ["Green", "Test", "Foo"]
    assert meta.get_attribute(attribute) == ["Green", "Test", "Foo"]

    tag_expected = "Test"
    tag_got = meta.keywords.pop(1)
    assert tag_got == tag_expected
    assert meta.keywords == ["Green", "Foo"]
    assert meta.get_attribute(attribute) == ["Green", "Foo"]


# def test_description(temp_file):
#     """ test string functions on one of the str attributes """
#     from osxmetadata import OSXMetaData

#     meta = OSXMetaData(temp_file)
#     meta.description = "Foo"
#     assert meta.description == "Foo"
#     assert meta.get_attribute("description") == "Foo"

#     meta.description += " Bar"
#     assert meta.description == "Foo Bar"
#     assert meta.get_attribute("description") == "Foo Bar"

#     meta.description = None
#     assert meta.description is None
#     assert meta.get_attribute("description") is None

#     meta.description = "Foo"
#     assert meta.description == "Foo"
#     assert meta.get_attribute("description") == "Foo"
