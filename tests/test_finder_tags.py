"""Test Finder tags (_KMDItemUserTags) on a file."""

import pytest
from osxmetadata import *

from .conftest import snooze


def test_finder_tags(test_file):
    """Test Finder tags on a file."""

    md = OSXMetaData(test_file.name)
    assert not md.tags
    tag_values = [Tag("foo", FINDER_COLOR_NONE), Tag("bar", FINDER_COLOR_RED)]
    md.tags = tag_values
    snooze()
    assert sorted(md.tags) == sorted(tag_values)

    # test that tag names are being set correctly so NSURL can read them
    assert sorted(md.NSURLTagNamesKey) == ["bar", "foo"]

    # test that we can set tags to None
    md.tags = None
    snooze()
    assert not md.tags

    # test that we can set tags to empty list
    md.tags = []
    snooze()
    assert not md.tags


def test_finder_tags_get_set(test_file):
    """Test Finder tags on a file with get/set _kMDItemUserTags."""

    md = OSXMetaData(test_file.name)
    tag_values = [Tag("foo", FINDER_COLOR_NONE), Tag("bar", FINDER_COLOR_RED)]
    md.set(_kMDItemUserTags, tag_values)
    snooze()
    assert sorted(md.get(_kMDItemUserTags)) == sorted(tag_values)

    # test that tag names are being set correctly so NSURL can read them
    assert sorted(md.NSURLTagNamesKey) == ["bar", "foo"]

    # test that we can set tags to None
    md.set(_kMDItemUserTags, None)
    snooze()
    assert not md.get(_kMDItemUserTags)

    # test that we can set tags to empty list
    md.set(_kMDItemUserTags, [])
    snooze()
    assert not md.get(_kMDItemUserTags)
