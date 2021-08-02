"""Test osxphotos attributes """

from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest

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


def test_osxphotos_detected_text(temp_file):
    """test set_attribute, get_attribute, etc for osxphotos items"""
    from osxmetadata import OSXMetaData

    attribute = "osxphotos_detected_text"

    meta = OSXMetaData(temp_file)
    expected = [["Foo", 0.5]]
    meta.set_attribute(attribute, expected)
    got = meta.get_attribute(attribute)
    assert expected == got

    expected.append(["Bar", 0.7])
    meta.append_attribute(attribute, ["Bar", 0.7])
    assert meta.get_attribute(attribute) == expected

    expected.remove(["Bar", 0.7])
    meta.remove_attribute(attribute, ["Bar", 0.7])
    assert meta.get_attribute(attribute) == expected

    with pytest.raises(ValueError):
        meta.remove_attribute(attribute, "Bar")

    expected += [["Flooz", 0.3]]
    meta.update_attribute(attribute, ["Flooz", 0.3])
    assert meta.get_attribute(attribute) == expected

    expected.remove(["Flooz", 0.3])
    meta.discard_attribute(attribute, ["Flooz", 0.3])
    assert meta.get_attribute(attribute) == expected

    meta.clear_attribute(attribute)
    assert not meta.get_attribute(attribute)

    expected = [["Foo", 0.75]]
    meta.set_attribute(attribute, expected)
    got = meta.get_attribute(attribute)
    assert expected == got

    meta.set_attribute(attribute, [])
    assert not meta.get_attribute(attribute)


def test_osxphotos_detected_text_attribute(temp_file):
    """Test osxphotos.metadata:detected_text access by attribute"""
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    expected = [["Foo", 0.5]]
    meta.osxphotos_detected_text = expected
    got = meta.osxphotos_detected_text
    assert expected == got
    assert len(meta.osxphotos_detected_text) == 1

    expected.append(["Bar", 0.7])
    meta.osxphotos_detected_text.append(["Bar", 0.7])
    assert meta.osxphotos_detected_text == expected
    assert len(meta.osxphotos_detected_text) == 2

    expected.remove(["Bar", 0.7])
    meta.osxphotos_detected_text.remove(["Bar", 0.7])
    assert meta.osxphotos_detected_text == expected

    with pytest.raises(ValueError):
        meta.osxphotos_detected_text.remove("Bar")

    expected += [["Flooz", 0.3]]
    meta.osxphotos_detected_text.append(["Flooz", 0.3])
    assert meta.osxphotos_detected_text == expected

    expected.remove(["Flooz", 0.3])
    meta.osxphotos_detected_text.remove(["Flooz", 0.3])
    assert meta.osxphotos_detected_text == expected

    meta.osxphotos_detected_text = None
    assert not meta.osxphotos_detected_text
    assert meta.get_attribute("osxphotos_detected_text") is None

    expected = [["Foo", 0.75]]
    meta.osxphotos_detected_text = expected
    got = meta.osxphotos_detected_text
    assert expected == got

    meta.osxphotos_detected_text = []
    assert not meta.osxphotos_detected_text
