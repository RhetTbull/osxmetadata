"""Test datetime handling """

import datetime
import os
import plistlib
import time

import pytest

from osxmetadata import OSXMetaData
from osxmetadata.datetime_utils import *


def test_datetime_attribute_naive(test_file):
    """Test datetime attribute with naive value"""

    os.environ["TZ"] = "US/Pacific"
    time.tzset()

    # naive datetime in local timezone
    duedate = datetime.datetime(2022, 10, 1, 1, 2, 3)
    md = OSXMetaData(test_file.name)
    md.kMDItemDueDate = duedate
    assert md.kMDItemDueDate == duedate

    # Apple stores dates as UTC, so we need to convert to UTC
    xattr_datetime = md.get_xattr(
        "com.apple.metadata:kMDItemDueDate", decode=plistlib.loads
    )
    duedate_utc = datetime_remove_tz(
        datetime_naive_to_local(duedate).astimezone(datetime.timezone.utc)
    )
    assert xattr_datetime == duedate_utc


def test_datetime_attribute_tz_aware(test_file):
    """Test datetime attribute with timezone aware value"""

    os.environ["TZ"] = "US/Pacific"
    time.tzset()

    # naive datetime in local timezone
    duedate = datetime_naive_to_local(datetime.datetime(2022, 10, 1, 1, 2, 3))
    md = OSXMetaData(test_file.name)
    md.kMDItemDueDate = duedate
    assert md.kMDItemDueDate == datetime_remove_tz(duedate)

    # Apple stores dates as UTC, so we need to convert to UTC
    xattr_datetime = md.get_xattr(
        "com.apple.metadata:kMDItemDueDate", decode=plistlib.loads
    )
    duedate_utc = datetime_remove_tz(duedate.astimezone(datetime.timezone.utc))
    assert xattr_datetime == duedate_utc
