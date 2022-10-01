"""Test osxmetadata get/set com.apple.FinderInfo xattr methods"""

import pytest

from osxmetadata import OSXMetaData, _kFinderStationaryPad


def test_stationarypad(test_file):
    """test get/set stationarypad methods"""

    attribute = "com.apple.metadata:kMDItemComment"
    value = "This is my comment"

    md = OSXMetaData(test_file.name)
    md.stationarypad = True
    assert md.stationarypad == True

    md.set(_kFinderStationaryPad, False)
    assert md.get(_kFinderStationaryPad) == False
