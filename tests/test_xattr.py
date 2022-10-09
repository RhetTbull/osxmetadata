"""Test osxmetadata get/set/remove xattr methods"""

import plistlib

import pytest

from osxmetadata import OSXMetaData

from .conftest import snooze


def test_xattr_get_set_remove(test_file):
    """test get/set/remove xattr methods"""

    attribute = "com.apple.metadata:kMDItemComment"
    value = "This is my comment"

    md = OSXMetaData(test_file.name)
    md.comment = value
    snooze()
    xattr_comment = md.get_xattr(attribute, decode=plistlib.loads)
    assert xattr_comment == value

    value = "This is my new comment"
    md.set_xattr(attribute, value, encode=plistlib.dumps)
    snooze()
    xattr_comment = md.get_xattr(attribute, decode=plistlib.loads)
    assert xattr_comment == value

    md.remove_xattr(attribute)
    with pytest.raises(KeyError):
        md.get_xattr(attribute, decode=plistlib.loads)
