""" Test int attributes """

from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
import platform

from osxmetadata.attributes import ATTRIBUTES


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
    (attr) for attr in sorted(list(ATTRIBUTES.keys())) if ATTRIBUTES[attr].class_ == int
]
ids = [
    attr for attr in sorted(list(ATTRIBUTES.keys())) if ATTRIBUTES[attr].class_ == int
]

test_data2 = [
    (attribute_name)
    for attribute_name in {
        ATTRIBUTES[attr].name
        for attr in sorted(ATTRIBUTES)
        if ATTRIBUTES[attr].class_ == int
    }
]
ids2 = [
    attribute_name
    for attribute_name in {
        ATTRIBUTES[attr].name
        for attr in sorted(ATTRIBUTES)
        if ATTRIBUTES[attr].class_ == int
    }
]


@pytest.mark.parametrize("attribute", test_data, ids=ids)
def test_str_attribute(temp_file, attribute):
    """test set_attribute, get_attribute, etc"""
    from osxmetadata import OSXMetaData
    from osxmetadata.constants import _FINDER_COMMENT_NAMES

    meta = OSXMetaData(temp_file)
    expected = 2
    meta.set_attribute(attribute, expected)
    got = meta.get_attribute(attribute)
    assert expected == got

    expected += 1
    meta.append_attribute(attribute, 1)
    assert meta.get_attribute(attribute) == expected

    meta.clear_attribute(attribute)
    assert meta.get_attribute(attribute) is None

    with pytest.raises(TypeError):
        meta.set_attribute(attribute, "")

    with pytest.raises(TypeError):
        meta.update_attribute(attribute, "foo")

    with pytest.raises(TypeError):
        meta.discard_attribute(attribute, "foo")

    with pytest.raises(TypeError):
        meta.remove_attribute(attribute, "foo")


@pytest.mark.parametrize("attribute", test_data2, ids=ids2)
def test_str_attribute_2(temp_file, attribute):
    """test getting and setting attribute by name"""
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    setattr(meta, attribute, 3)
    test_attr = getattr(meta, attribute)
    assert test_attr == 3
    assert meta.get_attribute(attribute) == 3


def test_rating(temp_file):
    """test int functions on one of the int attributes"""
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    meta.rating = 4
    assert meta.rating == 4
    assert meta.get_attribute("rating") == 4

    meta.rating += 1
    assert meta.rating == 5
    assert meta.get_attribute("rating") == 5

    meta.rating = None
    assert meta.rating is None
    assert meta.get_attribute("rating") is None

    meta.rating = 5
    assert meta.rating == 5
    assert meta.get_attribute("rating") == 5
