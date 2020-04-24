#!/usr/bin/env python

import datetime
from tempfile import NamedTemporaryFile

import pytest
from click.testing import CliRunner

from osxmetadata.attributes import ATTRIBUTES
from osxmetadata.classes import _AttributeList, _AttributeTagsList

# get list attribute names for string attributes for parameterized testing
test_names_str = [
    (attr) for attr in sorted(list(ATTRIBUTES.keys())) if ATTRIBUTES[attr].class_ == str
]
ids_str = [
    attr for attr in sorted(list(ATTRIBUTES.keys())) if ATTRIBUTES[attr].class_ == str
]

# list of list attributes of type str
test_names_list = [
    (attr)
    for attr in sorted(list(ATTRIBUTES.keys()))
    if ATTRIBUTES[attr].class_ in (_AttributeList, _AttributeTagsList)
    and ATTRIBUTES[attr].type_ == str
]
ids_list = [
    attr
    for attr in sorted(list(ATTRIBUTES.keys()))
    if ATTRIBUTES[attr].class_ in (_AttributeList, _AttributeTagsList)
    and ATTRIBUTES[attr].type_ == str
]


# list of list attributes of type datetime.datetime
test_names_dt = [
    (attr)
    for attr in sorted(list(ATTRIBUTES.keys()))
    if ATTRIBUTES[attr].class_ == _AttributeList
    and ATTRIBUTES[attr].type_ == datetime.datetime
]
ids_list_dt = [
    attr
    for attr in sorted(list(ATTRIBUTES.keys()))
    if ATTRIBUTES[attr].class_ == _AttributeList
    and ATTRIBUTES[attr].type_ == datetime.datetime
]


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


def parse_cli_output(output):
    """ helper for testing
        parse the CLI --list output and return value of all set attributes as dict """
    import re

    results = {}
    matches = re.findall(r"^(\w+)\s+.*\=\s+(.*)$", output, re.MULTILINE)
    for match in matches:
        results[match[0]] = match[1]
    return results


def test_cli_1(temp_file):
    import datetime
    from osxmetadata import OSXMetaData, kMDItemDownloadedDate
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "description",
            "Foo",
            "--append",
            "description",
            "Bar",
            "--list",
            temp_file,
        ],
    )
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    assert output["description"] == "FooBar"
    meta = OSXMetaData(temp_file)
    assert meta.description == "FooBar"

    result = runner.invoke(
        cli,
        [
            "--update",
            "keywords",
            "foo",
            "--update",
            "keywords",
            "bar",
            "--remove",
            "keywords",
            "foo",
            "--list",
            temp_file,
        ],
    )
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    assert output["keywords"] == "['bar']"
    meta = OSXMetaData(temp_file)
    assert meta.keywords == ["bar"]

    dt = "2020-02-23"
    result = runner.invoke(cli, ["--set", "downloadeddate", dt, "--list", temp_file])
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    assert output["downloadeddate"] == "['2020-02-23T00:00:00']"
    expected_dt = datetime.datetime.fromisoformat(dt)
    meta = OSXMetaData(temp_file)
    assert meta.get_attribute(kMDItemDownloadedDate) == [expected_dt]
    assert meta.downloadeddate == [expected_dt]

    result = runner.invoke(cli, ["--clear", "description", temp_file])
    assert result.exit_code == 0
    meta = OSXMetaData(temp_file)
    assert meta.description is None


@pytest.mark.parametrize("attribute", test_names_str, ids=ids_str)
def test_str_attributes(temp_file, attribute):
    from osxmetadata import OSXMetaData, ATTRIBUTES
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--set", attribute, "Foo", "--append", attribute, "Bar", "--list", temp_file],
    )
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    attr_short_name = ATTRIBUTES[attribute].name
    assert output[attr_short_name] == "FooBar"
    meta = OSXMetaData(temp_file)
    assert meta.get_attribute(attribute) == "FooBar"


@pytest.mark.parametrize("attribute", test_names_list, ids=ids_list)
def test_list_attributes(temp_file, attribute):
    from osxmetadata import OSXMetaData, ATTRIBUTES
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli, ["--set", attribute, "Foo", "--set", attribute, "Bar", "--list", temp_file]
    )
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    attr_short_name = ATTRIBUTES[attribute].name
    assert output[attr_short_name] == "['Foo', 'Bar']"
    meta = OSXMetaData(temp_file)
    assert meta.get_attribute(attribute) == ["Foo", "Bar"]

    result = runner.invoke(
        cli,
        [
            "--append",
            attribute,
            "Green",
            "--remove",
            attribute,
            "Foo",
            "--list",
            temp_file,
        ],
    )
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    attr_short_name = ATTRIBUTES[attribute].name
    assert output[attr_short_name] == "['Bar', 'Green']"


@pytest.mark.parametrize("attribute", test_names_dt, ids=ids_list_dt)
def test_datetime_list_attributes(temp_file, attribute):
    from osxmetadata import OSXMetaData, ATTRIBUTES
    from osxmetadata.__main__ import cli

    dt = datetime.datetime.now()
    dt_str = dt.isoformat()

    runner = CliRunner()
    result = runner.invoke(cli, ["--set", attribute, dt_str, "--list", temp_file])
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    attr_short_name = ATTRIBUTES[attribute].name
    assert output[attr_short_name] == f"['{dt_str}']"
    meta = OSXMetaData(temp_file)
    assert meta.get_attribute(attribute) == [dt]


def test_get_json(temp_file):
    import json
    import pathlib
    from osxmetadata import OSXMetaData, ATTRIBUTES, __version__
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli, ["--set", "tags", "foo", "--set", "tags", "bar", temp_file]
    )
    result = runner.invoke(cli, ["--get", "tags", "--json", temp_file])
    assert result.exit_code == 0
    json_ = json.loads(result.stdout)
    assert json_["com.apple.metadata:_kMDItemUserTags"] == ["foo", "bar"]
    assert json_["_version"] == __version__
    assert json_["_filename"] == pathlib.Path(temp_file).name


def test_list_json(temp_file):
    import json
    import pathlib
    from osxmetadata import OSXMetaData, ATTRIBUTES, __version__
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli, ["--set", "tags", "foo", "--set", "tags", "bar", temp_file]
    )
    result = runner.invoke(cli, ["--list", "--json", temp_file])
    assert result.exit_code == 0
    json_ = json.loads(result.stdout)
    assert json_["com.apple.metadata:_kMDItemUserTags"] == ["foo", "bar"]
    assert json_["_version"] == __version__
    assert json_["_filename"] == pathlib.Path(temp_file).name


def test_cli_error_json(temp_file):
    from osxmetadata import OSXMetaData, ATTRIBUTES
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--set", "tags", "foo", "--json", temp_file])
    assert result.exit_code == 2
    assert "--json can only be used with --get or --list" in result.stdout


def test_cli_error_bad_attribute(temp_file):
    from osxmetadata import OSXMetaData, ATTRIBUTES
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--set", "foo", "bar", temp_file])
    assert result.exit_code == 2
    assert "Invalid attribute foo" in result.stdout


def test_cli_error(temp_file):
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--set", temp_file])
    assert result.exit_code == 2
    assert "Error: --set option requires 2 arguments" in result.stdout


def test_cli_backup_restore(temp_file):
    import pathlib
    from osxmetadata import OSXMetaData, ATTRIBUTES
    from osxmetadata.constants import _BACKUP_FILENAME
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "tags",
            "Foo",
            "--set",
            "tags",
            "Bar",
            "--set",
            "comment",
            "Hello World!",
            "--list",
            temp_file,
        ],
    )
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    assert output["tags"] == "['Foo', 'Bar']"
    meta = OSXMetaData(temp_file)
    assert meta.get_attribute("tags") == ["Foo", "Bar"]
    assert meta.get_attribute("comment") == "Hello World!"

    # test creation of backup file
    result = runner.invoke(cli, ["--backup", temp_file])
    assert result.exit_code == 0
    backup_file = pathlib.Path(pathlib.Path(temp_file).parent) / _BACKUP_FILENAME
    assert backup_file.exists()

    # clear the attributes to see if they can be restored
    meta.clear_attribute("tags")
    meta.clear_attribute("comment")
    assert meta.tags == []
    assert meta.comment == None

    result = runner.invoke(cli, ["--restore", temp_file])
    assert result.exit_code == 0
    assert meta.tags == ["Foo", "Bar"]
    assert meta.comment == "Hello World!"


def test_cli_backup_restore_2(temp_file):
    # test set during restore
    import pathlib
    from osxmetadata import OSXMetaData, ATTRIBUTES
    from osxmetadata.constants import _BACKUP_FILENAME
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "tags",
            "Foo",
            "--set",
            "tags",
            "Bar",
            "--set",
            "comment",
            "Hello World!",
            "--list",
            temp_file,
        ],
    )
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    assert output["tags"] == "['Foo', 'Bar']"
    meta = OSXMetaData(temp_file)
    assert meta.get_attribute("tags") == ["Foo", "Bar"]
    assert meta.get_attribute("comment") == "Hello World!"

    # test creation of backup file
    result = runner.invoke(cli, ["--backup", temp_file])
    assert result.exit_code == 0
    backup_file = pathlib.Path(pathlib.Path(temp_file).parent) / _BACKUP_FILENAME
    assert backup_file.exists()

    # clear the attributes to see if they can be restored
    meta.clear_attribute("tags")
    meta.clear_attribute("comment")
    assert meta.tags == []
    assert meta.comment == None

    result = runner.invoke(
        cli,
        [
            "--restore",
            "--append",
            "tags",
            "Flooz",
            "--set",
            "keywords",
            "FooBar",
            temp_file,
        ],
    )
    assert result.exit_code == 0
    assert meta.tags == ["Foo", "Bar", "Flooz"]
    assert meta.comment == "Hello World!"
    assert meta.keywords == ["FooBar"]


def test_cli_mirror(temp_file):
    import datetime
    from osxmetadata import OSXMetaData
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "comment",
            "Foo",
            "--set",
            "findercomment",
            "Bar",
            "--set",
            "keywords",
            "foo",
            "--set",
            "tags",
            "bar",
            "--list",
            temp_file,
        ],
    )
    assert result.exit_code == 0
    meta = OSXMetaData(temp_file)
    assert meta.tags == ["bar"]
    assert meta.keywords == ["foo"]
    assert meta.findercomment == "Bar"
    assert meta.comment == "Foo"

    result = runner.invoke(
        cli,
        [
            "--mirror",
            "keywords",
            "tags",
            "--mirror",
            "comment",
            "findercomment",
            temp_file,
        ],
    )

    assert result.exit_code == 0
    assert meta.keywords == ["bar", "foo"]
    assert meta.tags == ["bar", "foo"]
    assert meta.findercomment == "Bar"
    assert meta.comment == "Bar"


def test_cli_mirror_bad_args(temp_file):
    import datetime
    from osxmetadata import OSXMetaData
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--mirror", "keywords", "comment", temp_file])
    assert result.exit_code == 2
    assert "incompatible types" in result.output

    result = runner.invoke(cli, ["--mirror", "downloadeddate", "tags", temp_file])
    assert result.exit_code == 2
    assert "incompatible types" in result.output


def test_cli_wipe(temp_file):
    from osxmetadata import OSXMetaData
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "comment",
            "Foo",
            "--set",
            "findercomment",
            "Bar",
            "--set",
            "keywords",
            "foo",
            "--set",
            "tags",
            "bar",
            "--list",
            temp_file,
        ],
    )
    assert result.exit_code == 0
    meta = OSXMetaData(temp_file)
    assert meta.tags == ["bar"]
    assert meta.keywords == ["foo"]
    assert meta.findercomment == "Bar"
    assert meta.comment == "Foo"

    result = runner.invoke(cli, ["--wipe", temp_file])
    assert result.exit_code == 0
    assert meta.tags == []
    assert meta.keywords == []
    assert meta.findercomment is None
    assert meta.comment is None


def test_cli_wipe_2(temp_file):
    # test wipe then set
    from osxmetadata import OSXMetaData
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "comment",
            "Foo",
            "--set",
            "findercomment",
            "Bar",
            "--set",
            "keywords",
            "foo",
            "--set",
            "tags",
            "bar",
            "--list",
            temp_file,
        ],
    )
    assert result.exit_code == 0
    meta = OSXMetaData(temp_file)
    assert meta.tags == ["bar"]
    assert meta.keywords == ["foo"]
    assert meta.findercomment == "Bar"
    assert meta.comment == "Foo"

    result = runner.invoke(
        cli, ["--wipe", "--set", "comment", "Hello World!", temp_file]
    )
    assert result.exit_code == 0
    assert meta.tags == []
    assert meta.keywords == []
    assert meta.findercomment is None
    assert meta.comment == "Hello World!"


def test_cli_copy_from(temp_file):
    # test copy from source file
    from osxmetadata import OSXMetaData
    from osxmetadata.__main__ import cli

    TESTDIR = None
    source_file = NamedTemporaryFile(dir=TESTDIR)
    source_filename = source_file.name

    meta_source = OSXMetaData(source_filename)
    meta_source.tags = ["bar"]
    meta_source.keywords = ["foo"]
    meta_source.findercomment = "Bar"
    meta_source.comment = "Foo"

    runner = CliRunner()
    result = runner.invoke(cli, ["--copyfrom", source_filename, temp_file])
    assert result.exit_code == 0
    meta = OSXMetaData(temp_file)
    assert meta.tags == ["bar"]
    assert meta.keywords == ["foo"]
    assert meta.findercomment == "Bar"
    assert meta.comment == "Foo"

    source_file.close()


def test_cli_copy_from_2(temp_file):
    # test copy from source file with setting etc
    from osxmetadata import OSXMetaData
    from osxmetadata.__main__ import cli

    TESTDIR = None
    source_file = NamedTemporaryFile(dir=TESTDIR)
    source_filename = source_file.name

    meta_source = OSXMetaData(source_filename)
    meta_source.tags = ["bar"]
    meta_source.keywords = ["foo"]
    meta_source.findercomment = "Bar"
    meta_source.comment = "Foo"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--copyfrom",
            source_filename,
            temp_file,
            "--set",
            "tags",
            "FOOBAR",
            "--append",
            "findercomment",
            "Foo",
        ],
    )
    assert result.exit_code == 0
    meta = OSXMetaData(temp_file)
    assert meta.tags == ["FOOBAR"]
    assert meta.keywords == ["foo"]
    assert meta.findercomment == "BarFoo"
    assert meta.comment == "Foo"

    source_file.close()


def test_cli_verbose(temp_file):
    from osxmetadata import OSXMetaData
    from osxmetadata.__main__ import cli

    TESTDIR = None
    source_file = NamedTemporaryFile(dir=TESTDIR)
    source_filename = source_file.name

    meta_source = OSXMetaData(source_filename)
    meta_source.tags = ["bar"]
    meta_source.keywords = ["foo"]
    meta_source.findercomment = "Bar"
    meta_source.comment = "Foo"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--wipe",
            "--set",
            "keywords",
            "test",
            "--list",
            "--get",
            "keywords",
            "--clear",
            "keywords",
            "--remove",
            "keywords",
            "test",
            "--update",
            "keywords",
            "foo",
            "--mirror",
            "keywords",
            "tags",
            "--backup",
            "--verbose",
            "--copyfrom",
            source_filename,
            temp_file,
        ],
    )
    assert result.exit_code == 0
    output = result.output
    assert "Processing file" in output
    assert "No metadata to wipe from" in output
    assert "Copying attributes from" in output
    assert "Copying com.apple.metadata:_kMDItemUserTags" in output
    assert "Copying com.apple.metadata:kMDItemComment" in output
    assert "Copying com.apple.metadata:kMDItemKeywords" in output
    assert "Copying com.apple.metadata:kMDItemFinderComment" in output
    assert "Clearing keywords" in output
    assert "Setting keywords=test" in output
    assert "Updating keywords=foo" in output
    assert "Removing keywords" in output
    assert "Mirroring keywords tags" in output
    assert "Backing up attribute data" in output

    source_file.close()


def test_cli_verbose_short_opts(temp_file):
    from osxmetadata import OSXMetaData
    from osxmetadata.__main__ import cli

    TESTDIR = None
    source_file = NamedTemporaryFile(dir=TESTDIR)
    source_filename = source_file.name

    meta_source = OSXMetaData(source_filename)
    meta_source.tags = ["bar"]
    meta_source.keywords = ["foo"]
    meta_source.findercomment = "Bar"
    meta_source.comment = "Foo"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "-X",
            "-s",
            "keywords",
            "test",
            "-l",
            "-g",
            "keywords",
            "-c",
            "keywords",
            "-r",
            "keywords",
            "test",
            "-u",
            "keywords",
            "foo",
            "-m",
            "keywords",
            "tags",
            "-V",
            "-B",
            "-f",
            source_filename,
            temp_file,
        ],
    )
    assert result.exit_code == 0
    output = result.output
    assert "Processing file" in output
    assert "No metadata to wipe from" in output
    assert "Copying attributes from" in output
    assert "Copying com.apple.metadata:_kMDItemUserTags" in output
    assert "Copying com.apple.metadata:kMDItemComment" in output
    assert "Copying com.apple.metadata:kMDItemKeywords" in output
    assert "Copying com.apple.metadata:kMDItemFinderComment" in output
    assert "Clearing keywords" in output
    assert "Setting keywords=test" in output
    assert "Updating keywords=foo" in output
    assert "Removing keywords" in output
    assert "Mirroring keywords tags" in output
    assert "Backing up attribute data" in output

    source_file.close()


def test_cli_version():
    from osxmetadata import OSXMetaData, __version__
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["-v"])
    assert result.exit_code == 0
    assert f"version {__version__}" in result.output

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert f"version {__version__}" in result.output


def test_cli_downloadeddate(temp_file):
    # pass ISO 8601 format with timezone, get back naive local time
    import datetime
    from osxmetadata import OSXMetaData, kMDItemDownloadedDate
    from osxmetadata.datetime_utils import (
        datetime_naive_to_utc,
        datetime_utc_to_local,
        datetime_remove_tz,
    )
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    dt = "2020-02-23:00:00:00+00:00"  # UTC time
    utc_time = datetime.datetime.fromisoformat(dt)
    local_time = datetime_remove_tz(datetime_utc_to_local(utc_time))

    result = runner.invoke(cli, ["--set", "downloadeddate", dt, "--list", temp_file])
    assert result.exit_code == 0

    output = parse_cli_output(result.stdout)
    assert output["downloadeddate"] == f"['{local_time.isoformat()}']"

    meta = OSXMetaData(temp_file)
    meta.tz_aware = True
    assert meta.get_attribute(kMDItemDownloadedDate) == [utc_time]
    assert meta.downloadeddate == [utc_time]
