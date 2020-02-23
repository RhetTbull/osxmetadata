#!/usr/bin/env python

import platform
from tempfile import NamedTemporaryFile

import pytest
from click.testing import CliRunner

from osxmetadata.attributes import ATTRIBUTES
from osxmetadata.classes import _AttributeList


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


def test_cli_1(temp_file):
    from osxmetadata import OSXMetaData
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--set", "description", "Foo", "--append", "description", "Bar", temp_file],
    )
    assert result.exit_code == 0

    meta = OSXMetaData(temp_file)
    assert meta.description == "FooBar"
