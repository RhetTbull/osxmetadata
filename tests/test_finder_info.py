"""Test osxmetadata get/set com.apple.FinderInfo xattr methods"""

import pytest

from osxmetadata import (
    ALL_ATTRIBUTES,
    OSXMetaData,
    Tag,
    _kFinderColor,
    _kFinderInfo,
    _kFinderStationaryPad,
)
from osxmetadata.constants import (
    FINDER_COLOR_BLUE,
    FINDER_COLOR_GREEN,
    FINDER_COLOR_NONE,
)


def test_stationarypad(test_file):
    """test get/set stationarypad methods"""

    attribute = "com.apple.metadata:kMDItemComment"
    value = "This is my comment"

    md = OSXMetaData(test_file.name)
    md.stationarypad = True
    assert md.stationarypad == True

    md.set(_kFinderStationaryPad, False)
    assert md.get(_kFinderStationaryPad) == False


def test_finderinfo(test_file):
    """Test finderinfo attribute to get raw bytes"""

    md = OSXMetaData(test_file.name)
    assert len(md.finderinfo) == 32

    assert (
        md.finderinfo
        == b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    md.stationarypad = True
    assert (
        md.finderinfo
        == b"\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )


def test_findercolor(test_file):
    """Test findercolor attribute to get/set color in the FinderInfo field"""

    md = OSXMetaData(test_file.name)
    assert md.findercolor == FINDER_COLOR_NONE
    md.findercolor = FINDER_COLOR_GREEN
    assert md.findercolor == FINDER_COLOR_GREEN

    # test that setting a tag color also sets the FinderInfo color
    md.findercolor = FINDER_COLOR_NONE
    md.tags = [Tag("Blue", color=FINDER_COLOR_BLUE)]
    assert md.findercolor == FINDER_COLOR_BLUE


def test_all_attributes():
    """Test that all Finder Info attributes are in ALL_ATTRIBUTES"""

    assert _kFinderStationaryPad in ALL_ATTRIBUTES
    assert _kFinderInfo in ALL_ATTRIBUTES
    assert _kFinderColor in ALL_ATTRIBUTES
