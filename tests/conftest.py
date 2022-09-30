"""Config for pytest"""

import datetime
import os
import time
import typing as t
from tempfile import NamedTemporaryFile

import pytest

TEST_IMAGE = "tests/test_image.jpg"
TEST_VIDEO = "tests/test_video.mov"
TEST_AUDIO = "tests/test_audio.m4a"


@pytest.fixture(scope="session")
def test_image():
    return TEST_IMAGE


@pytest.fixture(scope="session")
def test_video():
    return TEST_VIDEO


@pytest.fixture(scope="session")
def test_audio():
    return TEST_AUDIO


@pytest.fixture(scope="module")
def test_file():
    """Create a temporary file"""
    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with NamedTemporaryFile(dir=os.getcwd(), prefix="tmp_") as test_file:
        yield test_file


@pytest.fixture(scope="module")
def test_dir():
    """Create a temporary directory"""
    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with NamedTemporaryFile(dir=os.getcwd(), prefix="tmp_") as test_dir:
        yield test_dir


@pytest.fixture(scope="session")
def snooze():
    """Sleep for a bit to allow Finder to update metadata"""

    def _sleep():
        time.sleep(0.1)

    return _sleep


def value_for_type(
    type_: type,
) -> t.Union[str, float, bool, datetime.datetime, t.List[str]]:
    """Get test value for a given metadata attribute type"""
    if type_ == str:
        return "Hello World"
    elif type_ == float:
        return 42.0
    elif type_ == bool:
        return True
    elif type_ == datetime.datetime:
        return datetime.datetime(1995, 5, 31, 0, 0, 0)
    elif type_ == list:
        return ["a", "b"]
    else:
        raise ValueError(f"Unknown type: {type_}")
