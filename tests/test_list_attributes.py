#!/usr/bin/env python

from tempfile import NamedTemporaryFile

import pytest
import platform

from osxmetadata.attributes import ATTRIBUTES
from osxmetadata.classes import _AttributeList


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
    assert meta.get_attribute(attribute) == None

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
#     assert meta.description == None
#     assert meta.get_attribute("description") == None

#     meta.description = "Foo"
#     assert meta.description == "Foo"
#     assert meta.get_attribute("description") == "Foo"

