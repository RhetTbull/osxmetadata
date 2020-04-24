#!/usr/bin/env python

from tempfile import NamedTemporaryFile

import pytest
import platform


@pytest.fixture
def temp_file():

    # TESTDIR for temporary files usually defaults to "/tmp",
    # which may not have XATTR support (e.g. tmpfs);
    # manual override here.
    TESTDIR = None
    tempfile = NamedTemporaryFile(dir=TESTDIR)
    tempfilename = tempfile.name
    yield tempfilename
    tempfile.close()


def test_download_date(temp_file):
    from osxmetadata import OSXMetaData
    import datetime

    meta = OSXMetaData(temp_file)
    dt = datetime.datetime.now()
    meta.downloadeddate = dt
    assert meta.downloadeddate == [dt]
    assert meta.get_attribute("downloadeddate") == [dt]


def test_download_date_tz_1A(temp_file):
    """ set naive time but return tz_aware """
    from osxmetadata import OSXMetaData
    from osxmetadata.datetime_utils import datetime_naive_to_local
    import datetime

    meta = OSXMetaData(temp_file, tz_aware=True)
    dt = datetime.datetime.now()
    meta.set_attribute("downloadeddate", dt)
    dt_tz = datetime_naive_to_local(dt)
    assert meta.downloadeddate == [dt_tz]
    assert meta.get_attribute("downloadeddate") == [dt_tz]


def test_download_date_tz_1B(temp_file):
    """ set naive time but return tz_aware """
    from osxmetadata import OSXMetaData
    from osxmetadata.datetime_utils import datetime_naive_to_local
    import datetime

    meta = OSXMetaData(temp_file, tz_aware=True)
    dt = datetime.datetime.now()
    meta.downloadeddate = dt
    dt_tz = datetime_naive_to_local(dt)
    assert meta.downloadeddate == [dt_tz]
    assert meta.get_attribute("downloadeddate") == [dt_tz]


def test_download_date_tz_2(temp_file):
    """ set tz_aware and return tz_aware """
    from osxmetadata import OSXMetaData
    from osxmetadata.datetime_utils import datetime_naive_to_local
    import datetime

    meta = OSXMetaData(temp_file, tz_aware=True)
    dt = datetime.datetime.now()
    dt_tz = datetime_naive_to_local(dt)
    meta.downloadeddate = dt_tz
    assert meta.downloadeddate == [dt_tz]
    assert meta.get_attribute("downloadeddate") == [dt_tz]


def test_download_date_tz_3(temp_file):
    """ set tz_aware and return naive """
    from osxmetadata import OSXMetaData
    from osxmetadata.datetime_utils import datetime_naive_to_local
    import datetime

    meta = OSXMetaData(temp_file, tz_aware=False)
    dt = datetime.datetime.now()
    dt_tz = datetime_naive_to_local(dt)
    meta.downloadeddate = dt_tz
    assert meta.downloadeddate == [dt]
    assert meta.get_attribute("downloadeddate") == [dt]


def test_download_date_tz_4(temp_file):
    """ test tz_aware property """
    from osxmetadata import OSXMetaData
    from osxmetadata.datetime_utils import datetime_naive_to_local
    import datetime

    meta = OSXMetaData(temp_file)
    dt = datetime.datetime.now()

    # test tz_aware
    assert not meta.tz_aware
    meta.tz_aware = True
    assert meta.tz_aware

    # test tz_aware
    dt_tz = datetime_naive_to_local(dt)
    meta.downloadeddate = dt_tz
    assert meta.downloadeddate == [dt_tz]
    assert meta.get_attribute("downloadeddate") == [dt_tz]

    # test timezone == UTC
    dld = meta.downloadeddate[0]
    tz = dld.tzinfo.tzname(dld)
    assert tz == "UTC"

    # turn tz_aware off
    meta.tz_aware = False
    assert meta.downloadeddate == [dt]
    assert meta.get_attribute("downloadeddate") == [dt]
    assert meta.downloadeddate[0].tzinfo == None
