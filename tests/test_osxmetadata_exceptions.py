"""Test exceptions raised by OSXMetaData"""

import datetime

import pytest

from osxmetadata import OSXMetaData


def test_get_invalid_attribute(test_file):
    """Test get invalid attribute"""
    md = OSXMetaData(test_file.name)
    with pytest.raises(AttributeError):
        md.invalid_attribute


def test_set_invalid_attribute(test_file):
    """Test set invalid attribute"""
    md = OSXMetaData(test_file.name)
    with pytest.raises(AttributeError):
        md.invalid_attribute = "value"


def test_set_readonly_attribute(test_file):
    """Test set readonly attribute"""
    md = OSXMetaData(test_file.name)
    with pytest.raises(AttributeError):
        md.kMDItemDateAdded = datetime.datetime.now()


def test_get_invalid_key(test_file):
    """Test get invalid key"""
    md = OSXMetaData(test_file.name)
    with pytest.raises(KeyError):
        md["invalid_key"]


def test_set_invalid_key(test_file):
    """Test set invalid key"""
    md = OSXMetaData(test_file.name)
    with pytest.raises(KeyError):
        md["invalid_key"] = "value"


def test_set_readonly_key(test_file):
    """Test set readonly key"""
    md = OSXMetaData(test_file.name)
    with pytest.raises(KeyError):
        md["kMDItemDateAdded"] = datetime.datetime.now()
