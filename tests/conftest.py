"""Config for pytest"""

import datetime
import os
import time
import typing as t
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest

TEST_IMAGE = "tests/test_image.jpg"
TEST_VIDEO = "tests/test_video.mov"
TEST_AUDIO = "tests/test_audio.m4a"

# how long to wait for metadata to be written to disk
# if running in GitHub Actions, wait longer
GH_ACTION_SNOOZE = 10.0
SNOOZE_TIME = GH_ACTION_SNOOZE if os.environ.get("GITHUB_ACTION") else 0.1
# some tests need a longer snooze time
LONG_SNOOZE = GH_ACTION_SNOOZE if os.environ.get("GITHUB_ACTION") else 3.0
# Finder comments need more time to be written to disk
FINDER_COMMENT_SNOOZE = LONG_SNOOZE

def snooze(seconds: float = SNOOZE_TIME) -> None:
    """Sleep for a bit to allow Finder to update metadata"""
    time.sleep(seconds)


@pytest.fixture(scope="session")
def test_image():
    return TEST_IMAGE


@pytest.fixture(scope="session")
def test_video():
    return TEST_VIDEO


@pytest.fixture(scope="session")
def test_audio():
    return TEST_AUDIO


@pytest.fixture(scope="function")
def test_file():
    """Create a temporary test file"""
    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with NamedTemporaryFile(dir=os.getcwd(), prefix="tmp_") as test_file:
        yield test_file


@pytest.fixture(scope="function")
def test_file2():
    """Create a temporary test file"""
    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with NamedTemporaryFile(dir=os.getcwd(), prefix="tmp_") as test_file:
        yield test_file


@pytest.fixture(scope="function")
def test_dir():
    """Create a temporary directory"""
    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with TemporaryDirectory(dir=os.getcwd(), prefix="tmp_") as test_dir:
        yield test_dir


def value_for_type(
    type_: type,
) -> t.Union[
    str, float, bool, datetime.datetime, t.List[str], t.List[datetime.datetime]
]:
    """Get test value for a given metadata attribute type"""
    if type_ == "str":
        return "Hello World"
    elif type_ == "float":
        return 42.0
    elif type_ == "bool":
        return True
    elif type_ == "datetime.datetime":
        return datetime.datetime(1995, 5, 31, 0, 0, 0)
    elif type_ == "list":
        return ["a", "b"]
    elif type_ == "list[datetime.datetime]":
        return [datetime.datetime(1995, 5, 31, 0, 0, 0)]
    else:
        raise ValueError(f"Unknown type: {type_}")
