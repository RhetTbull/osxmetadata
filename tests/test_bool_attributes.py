""" Test bool attributes """

import platform
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
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
    (attr)
    for attr in sorted(list(ATTRIBUTES.keys()))
    if ATTRIBUTES[attr].class_ == bool
]
ids = [
    attr for attr in sorted(list(ATTRIBUTES.keys())) if ATTRIBUTES[attr].class_ == bool
]

test_data2 = [
    (attribute_name)
    for attribute_name in {
        ATTRIBUTES[attr].name
        for attr in sorted(ATTRIBUTES)
        if ATTRIBUTES[attr].class_ == bool
    }
]
ids2 = [
    attribute_name
    for attribute_name in {
        ATTRIBUTES[attr].name
        for attr in sorted(ATTRIBUTES)
        if ATTRIBUTES[attr].class_ == bool
    }
]


@pytest.mark.parametrize("attribute", test_data, ids=ids)
def test_str_attribute(temp_file, attribute):
    """test set_attribute, get_attribute, etc"""
    from osxmetadata import OSXMetaData
    from osxmetadata.constants import _FINDER_COMMENT_NAMES

    meta = OSXMetaData(temp_file)
    expected = True
    meta.set_attribute(attribute, expected)
    got = meta.get_attribute(attribute)
    assert expected == got

    meta.set_attribute(attribute, not expected)
    assert not meta.get_attribute(attribute)

    meta.clear_attribute(attribute)
    assert meta.get_attribute(attribute) is None

    # test setting empty string
    # setting finder comment to empty string clears it
    # but other fields get set to empty string
    # this mirrors the way finder comments work in mdls
    meta.set_attribute(attribute, "")
    assert not meta.get_attribute(attribute)

    with pytest.raises(AttributeError):
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
    setattr(meta, attribute, True)
    test_attr = getattr(meta, attribute)
    assert test_attr
    assert meta.get_attribute(attribute)


def test_stationary(temp_file):
    """test string functions on one of the bool attributes"""
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    meta.stationary = True
    assert meta.stationary
    assert meta.get_attribute("stationary")

    meta.stationary = not meta.stationary
    assert not meta.stationary
    assert not meta.get_attribute("stationary")

    meta.stationary = None
    assert meta.stationary is None
    assert meta.get_attribute("stationary") is None

    meta.stationary = True
    assert meta.stationary
    assert meta.get_attribute("stationary")
