"""Test findercomment """

import pytest

from osxmetadata import OSXMetaData, kMDItemFinderComment

from .conftest import FINDER_COMMENT_SNOOZE, snooze


@pytest.mark.skip(
    "This should pass but on my machine (Catalina 10.15.7) it does not; the code runs correctly outside of pytest"
)
def test_finder_comments(test_file):

    md = OSXMetaData(test_file.name)
    fc = "This is my new comment"
    md.findercomment = fc
    # Finder comment is set via AppleScript events and may take a moment to update
    snooze(FINDER_COMMENT_SNOOZE)
    assert md.findercomment == fc

    fc += ", foo"
    md.findercomment += ", foo"
    snooze(FINDER_COMMENT_SNOOZE)
    assert md.findercomment == fc

    # set finder comment to "" deletes it as this mirrors Finder and mdls
    md.findercomment = ""
    snooze(FINDER_COMMENT_SNOOZE)
    assert not md.findercomment

    md.findercomment = "foo"
    snooze(FINDER_COMMENT_SNOOZE)
    assert md.findercomment == "foo"

    # set finder comment to None deletes it
    md.findercomment = None
    snooze(FINDER_COMMENT_SNOOZE)
    assert not md.findercomment

    # can we set findercomment after is was set to None?
    md.findercomment = "bar"
    snooze(FINDER_COMMENT_SNOOZE)
    assert md.findercomment == "bar"


@pytest.mark.skip(
    "This should pass but on my machine (Catalina 10.15.7) it does not; the code runs correctly outside of pytest"
)
def test_finder_comments_get_set(test_file):
    """test get/set attribute"""

    attribute = kMDItemFinderComment

    md = OSXMetaData(test_file.name)
    fc = "This is my new comment"
    md.set(attribute, fc)
    snooze(FINDER_COMMENT_SNOOZE)
    assert md.findercomment == fc

    fc += ", foo"
    md.findercomment += ", foo"
    snooze(FINDER_COMMENT_SNOOZE)
    assert md.findercomment == fc

    # set finder comment to "" deletes it as this mirrors mdls and Finder
    md.set(attribute, "")
    snooze(FINDER_COMMENT_SNOOZE)
    assert not md.get(attribute)

    md.set(attribute, "foo")
    snooze(FINDER_COMMENT_SNOOZE)
    assert md.get(attribute) == "foo"

    # set finder comment to None deletes it
    md.set(attribute, None)
    snooze(FINDER_COMMENT_SNOOZE)
    assert not md.get(attribute)

    # can we set findercomment after is was set to None?
    md.set(attribute, "bar")
    snooze(FINDER_COMMENT_SNOOZE)
    assert md.get(attribute) == "bar"


def test_finder_comments_dir(test_dir):
    """test get/set attribute but on a directory, not on a file"""

    attribute = kMDItemFinderComment

    md = OSXMetaData(test_dir)
    fc = "This is my new comment"
    md.set(attribute, fc)

    snooze(FINDER_COMMENT_SNOOZE)
    assert md.findercomment == fc

    md.findercomment += ", foo"
    fc += ", foo"

    snooze(FINDER_COMMENT_SNOOZE)
    assert md.findercomment == fc
