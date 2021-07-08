""" Test OSXMetaData class """
import platform
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest


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


def test_platform():
    # this module only works on Mac (darwin)
    import sys

    assert sys.platform == "darwin"


def test_name(temp_file):
    from osxmetadata import OSXMetaData
    import pathlib

    meta = OSXMetaData(temp_file)
    fname = pathlib.Path(temp_file)
    assert meta.name == fname.resolve().as_posix()


def test_to_json(temp_file):
    import json
    import pathlib
    from osxmetadata import OSXMetaData, Tag, __version__
    from osxmetadata.constants import FINDER_COLOR_NONE

    meta = OSXMetaData(temp_file)
    meta.tags = [Tag("foo"), Tag("bar")]
    json_ = json.loads(meta.to_json())

    assert json_["com.apple.metadata:_kMDItemUserTags"] == [
        ["foo", FINDER_COLOR_NONE],
        ["bar", FINDER_COLOR_NONE],
    ]
    assert json_["_version"] == __version__
    assert json_["_filename"] == pathlib.Path(temp_file).name


def test_restore(temp_file):
    from osxmetadata import OSXMetaData, Tag, kMDItemComment

    meta = OSXMetaData(temp_file)
    meta.tags = [Tag("foo"), Tag("bar")]
    meta.set_attribute(kMDItemComment, "Hello World!")
    attr_dict = meta.asdict()
    meta.tags = []
    meta.clear_attribute(kMDItemComment)

    assert meta.tags == []
    assert meta.comment is None

    meta._restore_attributes(attr_dict)
    assert meta.tags == [Tag("foo"), Tag("bar")]
    assert meta.get_attribute(kMDItemComment) == "Hello World!"


def test_file_not_exists(temp_file):
    from osxmetadata import OSXMetaData

    with pytest.raises(Exception):
        # kludge to create a file that almost certainly doesn't exist
        # TODO: make this less kludgy
        bad_filename = str(temp_file + temp_file)
        _ = OSXMetaData(bad_filename)
