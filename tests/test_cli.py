#!/usr/bin/env python

import datetime
from tempfile import NamedTemporaryFile

import pytest
from click.testing import CliRunner

from osxmetadata.attributes import ATTRIBUTES
from osxmetadata.classes import _AttributeList

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
    if ATTRIBUTES[attr].class_ == _AttributeList and ATTRIBUTES[attr].type_ == str
]
ids_list = [
    attr
    for attr in sorted(list(ATTRIBUTES.keys()))
    if ATTRIBUTES[attr].class_ == _AttributeList and ATTRIBUTES[attr].type_ == str
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


def test_cli_error(temp_file):
    from osxmetadata.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--set", temp_file])
    assert result.exit_code == 2
    assert "Error: --set option requires 2 arguments" in result.stdout
