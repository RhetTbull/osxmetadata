""" Test datetime.datetime attributes """
import datetime
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
    if ATTRIBUTES[attr].class_ == datetime.datetime
]
ids = [
    attr
    for attr in sorted(list(ATTRIBUTES.keys()))
    if ATTRIBUTES[attr].class_ == datetime.datetime
]

test_data2 = [
    (attribute_name)
    for attribute_name in {
        ATTRIBUTES[attr].name
        for attr in sorted(ATTRIBUTES)
        if ATTRIBUTES[attr].class_ == datetime.datetime
    }
]
ids2 = [
    attribute_name
    for attribute_name in {
        ATTRIBUTES[attr].name
        for attr in sorted(ATTRIBUTES)
        if ATTRIBUTES[attr].class_ == datetime.datetime
    }
]


@pytest.mark.parametrize("attribute", test_data, ids=ids)
def test_str_attribute(temp_file, attribute):
    """test set_attribute, get_attribute, etc"""
    from osxmetadata import OSXMetaData
    from osxmetadata.constants import _FINDER_COMMENT_NAMES

    meta = OSXMetaData(temp_file)
    expected = datetime.datetime(2021, 7, 8)
    meta.set_attribute(attribute, expected)
    got = meta.get_attribute(attribute)
    assert expected == got

    meta.clear_attribute(attribute)
    assert meta.get_attribute(attribute) == None

    # test setting empty string
    meta.set_attribute(attribute, "")
    assert meta.get_attribute(attribute) is None

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
    setattr(meta, attribute, datetime.datetime(2021, 7, 8))
    test_attr = getattr(meta, attribute)
    assert test_attr == datetime.datetime(2021, 7, 8)
    assert meta.get_attribute(attribute) == datetime.datetime(2021, 7, 8)


def test_duedate(temp_file):
    """test functions on one of the datetime attributes"""
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    meta.duedate = "2021-07-08"
    assert meta.duedate == datetime.datetime(2021, 7, 8)
    assert meta.get_attribute("duedate") == datetime.datetime(2021, 7, 8)

    meta.duedate = None
    assert meta.duedate is None
    assert meta.get_attribute("duedate") is None

    meta.duedate = datetime.datetime(2021, 7, 8)
    assert meta.duedate == datetime.datetime(2021, 7, 8)
    assert meta.get_attribute("duedate") == datetime.datetime(2021, 7, 8)
