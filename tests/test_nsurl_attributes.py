"""Test osxmetadata NSURL metadata tags"""

import pathlib

import pytest

from osxmetadata import OSXMetaData
from osxmetadata.attribute_data import (
    NSURL_RESOURCE_KEY_DATA,
)

from .conftest import snooze


@pytest.mark.parametrize("attribute_name", NSURL_RESOURCE_KEY_DATA.keys())
def test_nsurl_attributes_all(attribute_name, test_file):
    """Test that all NSURL attributes can be accessed without error"""

    md = OSXMetaData(test_file.name)
    md.get(attribute_name)


def test_nsurl_attribute_NSURLNameKey(test_file):
    """Test that NSURLNameKey can be read"""

    md = OSXMetaData(test_file.name)
    assert md.get("NSURLNameKey") == pathlib.Path(test_file.name).name


def test_nsurl_attribute_NSURLIsRegularFileKey(test_file):
    """Test that NSURLIsRegularFileKey can be read"""

    md = OSXMetaData(test_file.name)
    assert md.get("NSURLIsRegularFileKey") is True


def test_nsurl_attribute_NSURLTagNamesKey(test_file):
    """Test that NSURLTagNamesKey can be read and written"""

    md = OSXMetaData(test_file.name)
    assert md.get("NSURLTagNamesKey") is None
    md["NSURLTagNamesKey"] = ["a", "b"]
    snooze()
    assert md.NSURLTagNamesKey == ["a", "b"]
    md.NSURLTagNamesKey = []
    assert not md.NSURLTagNamesKey
