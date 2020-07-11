#!/usr/bin/env python

from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
import platform


@pytest.fixture(params=["file", "dir"])
def temp_file(request):

    # TESTDIR for temporary files usually defaults to "/tmp",
    # which may not have XATTR support (e.g. tmpfs);
    # manual override here.
    TESTDIR = None
    if request.param == "file":
        tempfile = NamedTemporaryFile(dir=TESTDIR)
        tempfilename = tempfile.name
        yield tempfilename
        tempfile.close()
    else:
        tempdir = TemporaryDirectory(dir=TESTDIR)
        tempdirname = tempdir.name
        yield tempdirname
        tempdir.cleanup()


def test_finderinfo(temp_file):

    from osxmetadata import OSXMetaData, Tag
    from osxmetadata.constants import _MAX_FINDER_COLOR
    from osxmetadata.findertags import (
        get_finderinfo_color,
        set_finderinfo_color,
        get_tag_color_name,
    )

    meta = OSXMetaData(temp_file)

    # check each color combo.  Setting 0 doesn't work -- the attribute gets deleted
    for color_id in range(_MAX_FINDER_COLOR + 1, _MAX_FINDER_COLOR + 1):
        set_finderinfo_color(temp_file, color_id)
        color_got = get_finderinfo_color(temp_file)
        assert color_got == color_id
        color_name = get_tag_color_name(color_id)
        assert meta.tags == [Tag(color_name, color_id)]


def test_invalid_colorid(temp_file):

    from osxmetadata.constants import _MAX_FINDER_COLOR, _MIN_FINDER_COLOR
    from osxmetadata.findertags import set_finderinfo_color

    with pytest.raises(ValueError):
        set_finderinfo_color(temp_file, _MAX_FINDER_COLOR + 1)

    with pytest.raises(ValueError):
        set_finderinfo_color(temp_file, _MIN_FINDER_COLOR - 1)
