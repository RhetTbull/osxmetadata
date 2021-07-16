""" Test finderinfo and findercolor """

from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest


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


def test_finderinfo_colorid(temp_file):

    from osxmetadata import OSXMetaData, Tag
    from osxmetadata.constants import _MAX_FINDER_COLOR
    from osxmetadata.findertags import get_tag_color_name

    meta = OSXMetaData(temp_file)

    # check each color combo.  Setting 0 doesn't work -- the attribute gets deleted
    for color_id in range(_MAX_FINDER_COLOR + 1, _MAX_FINDER_COLOR + 1):
        meta.finderinfo.color = color_id
        color_got = meta.finderinfo.color
        assert color_got == color_id
        color_name = get_tag_color_name(color_id)
        assert meta.tags == [Tag(color_name, color_id)]


def test_invalid_colorid(temp_file):
    from osxmetadata import OSXMetaData
    from osxmetadata.constants import _MAX_FINDER_COLOR, _MIN_FINDER_COLOR

    meta = OSXMetaData(temp_file)

    with pytest.raises(ValueError):
        meta.finderinfo.color = _MAX_FINDER_COLOR + 1

    with pytest.raises(ValueError):
        meta.finderinfo.color = _MIN_FINDER_COLOR - 1


def test_findercolor_colorid(temp_file):

    from osxmetadata import OSXMetaData, Tag
    from osxmetadata.constants import _MAX_FINDER_COLOR
    from osxmetadata.findertags import get_tag_color_name

    meta = OSXMetaData(temp_file)

    # check each color combo.  Setting 0 doesn't work -- the attribute gets deleted
    for color_id in range(_MAX_FINDER_COLOR + 1, _MAX_FINDER_COLOR + 1):
        meta.findercolor = color_id
        color_got = meta.findercolor
        assert color_got == color_id
        color_name = get_tag_color_name(color_id)
        assert meta.tags == [Tag(color_name, color_id)]


def test_invalid_findercolor_colorid(temp_file):
    from osxmetadata import OSXMetaData
    from osxmetadata.constants import _MAX_FINDER_COLOR, _MIN_FINDER_COLOR

    meta = OSXMetaData(temp_file)

    with pytest.raises(ValueError):
        meta.findercolor = _MAX_FINDER_COLOR + 1

    with pytest.raises(ValueError):
        meta.findercolor = _MIN_FINDER_COLOR - 1


def test_finderinfo_color_set_get_clear(temp_file):
    """Test ability to set_attribute, get_attribute, clear_attribute on finderinfo"""
    from osxmetadata import OSXMetaData, Tag
    from osxmetadata.constants import FINDER_COLOR_GREEN, FINDER_COLOR_BLUE
    from osxmetadata.findertags import get_tag_color_name

    meta = OSXMetaData(temp_file)

    assert meta.finderinfo.color == 0
    meta.finderinfo.color = FINDER_COLOR_GREEN
    assert meta.finderinfo.color == FINDER_COLOR_GREEN

    assert {"color": FINDER_COLOR_GREEN}.items() <= meta.get_attribute(
        "finderinfo"
    ).items()

    meta.set_attribute("finderinfo", {"color": FINDER_COLOR_BLUE})
    assert meta.finderinfo.color == FINDER_COLOR_BLUE

    meta.clear_attribute("finderinfo")
    assert meta.finderinfo.color == 0

    meta.finderinfo.color = FINDER_COLOR_GREEN
    meta.finderinfo.color = None
    assert meta.finderinfo.color == 0

    meta.finderinfo.color = FINDER_COLOR_GREEN
    meta.finderinfo = None
    assert meta.finderinfo.color == 0


def test_finderinfo_stationarypad_set_get_clear(temp_file):
    """Test ability to set_attribute, get_attribute, clear_attribute on finderinfo"""
    from osxmetadata import OSXMetaData, Tag

    meta = OSXMetaData(temp_file)

    assert meta.finderinfo.stationarypad == 0
    meta.finderinfo.stationarypad = True
    assert meta.finderinfo.stationarypad

    assert {"stationarypad": True}.items() <= meta.get_attribute("finderinfo").items()

    meta.set_attribute("finderinfo", {"stationarypad": True})
    assert meta.finderinfo.stationarypad

    meta.clear_attribute("finderinfo")
    assert not meta.finderinfo.stationarypad

    meta.finderinfo.stationarypad = None
    assert not meta.finderinfo.stationarypad

    # test string to bool
    meta.finderinfo.stationarypad = "True"
    assert meta.finderinfo.stationarypad


def test_finderinfo_stationarypad_and_color(temp_file):
    """Test ability to modify color and stationary pad independently"""
    from osxmetadata import OSXMetaData, Tag
    from osxmetadata.constants import (
        FINDER_COLOR_GREEN,
        FINDER_COLOR_BLUE,
        FINDER_COLOR_NONE,
    )

    meta = OSXMetaData(temp_file)

    assert meta.finderinfo.stationarypad == 0
    assert meta.finderinfo.color == FINDER_COLOR_NONE

    meta.finderinfo.stationarypad = True
    assert meta.finderinfo.stationarypad
    assert meta.finderinfo.color == FINDER_COLOR_NONE

    meta.finderinfo.color = FINDER_COLOR_GREEN
    assert meta.finderinfo.color == FINDER_COLOR_GREEN
    assert meta.finderinfo.stationarypad

    meta.finderinfo.stationarypad = False
    assert not meta.finderinfo.stationarypad
    assert meta.finderinfo.color == FINDER_COLOR_GREEN

    assert {
        "color": FINDER_COLOR_GREEN,
        "stationarypad": False,
    }.items() <= meta.get_attribute("finderinfo").items()

    meta.set_attribute("finderinfo", {"stationarypad": True})
    assert meta.finderinfo.stationarypad
    assert meta.finderinfo.color == FINDER_COLOR_GREEN

    meta.set_attribute("finderinfo", {"color": FINDER_COLOR_BLUE})
    assert meta.finderinfo.color == FINDER_COLOR_BLUE
    assert meta.finderinfo.stationarypad

    meta.finderinfo = {"color": FINDER_COLOR_GREEN}
    assert meta.finderinfo.color == FINDER_COLOR_GREEN
    assert meta.finderinfo.stationarypad

    meta.finderinfo = {"stationarypad": False}
    assert meta.finderinfo.color == FINDER_COLOR_GREEN
    assert not meta.finderinfo.stationarypad


def test_stationarypad(temp_file):
    """Test stationarypad attribute"""
    from osxmetadata import OSXMetaData

    meta = OSXMetaData(temp_file)
    assert not meta.stationarypad

    meta.stationarypad = True
    assert meta.stationarypad

    meta.stationarypad = 0
    assert not meta.stationarypad

    meta.stationarypad = 1
    assert meta.stationarypad

    meta.stationarypad = False
    assert not meta.stationarypad
    assert not meta.get_attribute("stationarypad")
    
    meta.set_attribute("stationarypad", True)
    assert meta.get_attribute("stationarypad")
