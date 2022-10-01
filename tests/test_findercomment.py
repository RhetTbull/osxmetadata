"""Test findercomment """

import pytest

from osxmetadata import OSXMetaData, kMDItemFinderComment


def test_finder_comments(test_file, snooze):

    md = OSXMetaData(test_file.name)
    fc = "This is my new comment"
    md.findercomment = fc
    # Finder comment is set via AppleScript events and may take a moment to update
    snooze()
    assert md.findercomment == fc
    md.findercomment += ", foo"
    fc += ", foo"
    snooze()
    assert md.findercomment == fc

    # set finder comment to "" deletes it as this mirrors Finder and mdls
    md.findercomment = ""
    snooze()
    assert not md.findercomment

    md.findercomment = "foo"
    snooze()
    assert md.findercomment == "foo"

    # set finder comment to None deletes it
    md.findercomment = None
    snooze()
    assert not md.findercomment

    # can we set findercomment after is was set to None?
    md.findercomment = "bar"
    snooze()
    assert md.findercomment == "bar"


def test_finder_comments_get_set(test_file, snooze):
    """test get/set attribute"""

    attribute = kMDItemFinderComment

    md = OSXMetaData(test_file.name)
    fc = "This is my new comment"
    md.set(attribute, fc)
    snooze()
    assert md.findercomment == fc
    md.findercomment += ", foo"
    fc += ", foo"
    snooze()
    assert md.findercomment == fc

    # set finder comment to "" deletes it as this mirrors mdls and Finder
    md.set(attribute, "")
    snooze()
    assert not md.get(attribute)

    md.set(attribute, "foo")
    snooze()
    assert md.get(attribute) == "foo"

    # set finder comment to None deletes it
    md.set(attribute, None)
    snooze()
    assert not md.get(attribute)

    # can we set findercomment after is was set to None?
    md.set(attribute, "bar")
    snooze()
    assert md.get(attribute) == "bar"


def test_finder_comments_dir(test_dir, snooze):
    """test get/set attribute but on a directory, not on a file"""

    attribute = kMDItemFinderComment

    md = OSXMetaData(test_dir.name)
    fc = "This is my new comment"
    md.set(attribute, fc)
    snooze()
    assert md.findercomment == fc
    md.findercomment += ", foo"
    fc += ", foo"
    snooze()
    assert md.findercomment == fc
