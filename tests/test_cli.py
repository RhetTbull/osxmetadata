""" Test osxmetadata command line interface """

import datetime
import glob
import json
import os
import pathlib

import pytest
from click.testing import CliRunner

from osxmetadata import *
from osxmetadata import __version__
from osxmetadata.__main__ import BACKUP_FILENAME, cli
from osxmetadata.backup import load_backup_file

from .conftest import FINDER_COMMENT_SNOOZE, LONG_SNOOZE, snooze


def parse_cli_output(output):
    """Helper for testing

    Parse the CLI --list output and return value of all set attributes as dict
    """
    import re

    matches = re.findall(r"^(\w+)\s+.*\=\s+(.*)$", output, re.MULTILINE)
    return {match[0]: match[1] for match in matches}


def test_cli_list(test_file):
    """Test --list"""

    md = OSXMetaData(test_file.name)
    md.authors = ["John Doe"]
    md.findercomment = "Hello World"
    md.tags = [Tag("test", 0)]
    md.description = "This is a test file"

    snooze(FINDER_COMMENT_SNOOZE)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--list", test_file.name],
    )
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    assert output["description"] == "This is a test file"
    assert output["findercomment"] == "Hello World"
    assert output["authors"] == "John Doe"
    assert output["tags"] == "test: 0"


def test_cli_version():
    """Test --version"""

    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_wipe(test_file):
    """Test --wipe"""

    md = OSXMetaData(test_file.name)
    md.authors = ["John Doe"]
    md.description = "This is a test file"

    snooze()
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--wipe", test_file.name],
    )
    snooze()
    assert result.exit_code == 0
    assert not md.authors
    assert not md.description


def test_cli_set(test_file):
    """Test --set"""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "authors",
            "John Doe",
            "--set",
            "tags",
            "test,0",
            "--set",
            "description",
            "Hello World",
            "--set",
            "description",
            "Goodbye World",  # this should overwrite the previous value
            test_file.name,
        ],
    )
    snooze()
    assert result.exit_code == 0
    md = OSXMetaData(test_file.name)
    assert md.authors == ["John Doe"]
    assert md.tags == [Tag("test", 0)]
    assert md.description == "Goodbye World"


def test_cli_set_multi_keywords_1(test_file):
    """Test --set with multiple keywords (#83)"""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "keywords",
            "Foo",
            "--set",
            "keywords",
            "Bar",
            test_file.name,
        ],
    )
    snooze()
    assert result.exit_code == 0
    md = OSXMetaData(test_file.name)
    assert sorted(md.keywords) == ["Bar", "Foo"]


def test_cli_set_multi_keywords_2(test_file):
    """Test --set, --append with multiple keywords (#83)"""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "keywords",
            "Foo",
            "--append",
            "keywords",
            "Bar",
            test_file.name,
        ],
    )
    snooze()
    assert result.exit_code == 0
    md = OSXMetaData(test_file.name)
    assert sorted(md.keywords) == ["Bar", "Foo"]


def test_cli_clear(test_file):
    """Test --clear"""

    md = OSXMetaData(test_file.name)
    md.authors = ["John Doe"]
    md.description = "This is a test file"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--clear", "authors", test_file.name],
    )
    snooze()
    assert result.exit_code == 0
    assert not md.authors
    assert md.description == "This is a test file"


def test_cli_append(test_file):
    """Test --append"""

    md = OSXMetaData(test_file.name)
    md.authors = ["John Doe"]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--append",
            "authors",
            "Jane Doe",
            "--append",  # append to empty attribute
            "tags",
            "test,0",
            test_file.name,
        ],
    )
    assert result.exit_code == 0
    assert md.authors == ["John Doe", "Jane Doe"]
    assert md.tags == [Tag("test", 0)]


def test_cli_set_then_append(test_file):
    """Test --set then --append"""

    md = OSXMetaData(test_file.name)
    md.authors = ["John Doe"]

    # set initial value
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "keywords",
            "foo",
            test_file.name,
        ],
    )
    assert result.exit_code == 0

    # set again and verify that it overwrites
    result = runner.invoke(
        cli,
        [
            "--set",
            "keywords",
            "bar",
            test_file.name,
        ],
    )
    assert result.exit_code == 0
    assert md.keywords == ["bar"]

    # append and verify that it appends
    result = runner.invoke(
        cli,
        [
            "--append",
            "keywords",
            "baz",
            test_file.name,
        ],
    )
    assert result.exit_code == 0
    assert sorted(md.keywords) == ["bar", "baz"]


def test_cli_get(test_file):
    """Test --get"""

    md = OSXMetaData(test_file.name)
    md.authors = ["John Doe"]
    md.description = "This is a test file"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--get", "authors", test_file.name],
    )
    assert result.exit_code == 0
    output = parse_cli_output(result.stdout)
    assert output["authors"] == "John Doe"


def test_cli_remove(test_file):
    """Test --remove"""

    md = OSXMetaData(test_file.name)
    md.authors = ["John Doe", "Jane Doe"]
    md.tags = [Tag("test", 0)]
    snooze()

    runner = CliRunner()
    result = runner.invoke(cli, ["--list", "--json", test_file.name])
    data = json.loads(result.output)
    assert sorted(data["kMDItemAuthors"]) == ["Jane Doe", "John Doe"]

    result = runner.invoke(
        cli,
        [
            "--remove",
            "authors",
            "John Doe",
            "--remove",
            "tags",
            "test,0",
            "--verbose",
            test_file.name,
        ],
    )
    assert result.exit_code == 0
    assert "Removing John Doe from authors" in result.output
    # for some reason this test fails without an additional delay
    # for the removed metadata to be updated on disk
    # without the additional delay, reading the metadata reads the previous value
    snooze(LONG_SNOOZE)

    result = runner.invoke(cli, ["--list", "--json", test_file.name])
    data = json.loads(result.output)
    assert data["kMDItemAuthors"] == ["Jane Doe"]


def test_cli_remove_tags_without_color(test_file):
    """Test --remove tags without specifying color (#106)"""

    runner = CliRunner()
    result = runner.invoke(cli, ["--set", "tags", ".Test,red", test_file.name])
    snooze(LONG_SNOOZE)

    md = OSXMetaData(test_file.name)
    assert md.tags == [Tag(".Test", 6)]

    result = runner.invoke(
        cli,
        ["--remove", "tags", ".Test", test_file.name],
    )
    assert result.exit_code == 0

    snooze(LONG_SNOOZE)
    md = OSXMetaData(test_file.name)
    assert not md.tags


def test_cli_mirror(test_file):
    """Test --mirror"""

    md = OSXMetaData(test_file.name)
    md.description = "This is a test file"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--mirror",
            "comment",
            "description",
            test_file.name,
            "--verbose",
        ],
    )
    snooze()
    assert result.exit_code == 0
    assert "Mirroring" in result.stdout

    md = OSXMetaData(test_file.name)
    assert md.description == "This is a test file"


def test_cli_copyfrom(test_file, test_file2):
    """Test --copyfrom"""

    md = OSXMetaData(test_file.name)
    md.description = "This is a test file"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--copyfrom",
            test_file.name,
            test_file2.name,
        ],
    )
    snooze()
    assert result.exit_code == 0

    md = OSXMetaData(test_file2.name)
    assert md.description == "This is a test file"


def test_cli_walk(test_dir):
    """test --walk"""

    dirname = pathlib.Path(test_dir)
    os.makedirs(dirname / "temp" / "subfolder1")
    os.makedirs(dirname / "temp" / "subfolder2")
    (dirname / "temp" / "temp1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.txt").touch()

    runner = CliRunner()
    result = runner.invoke(cli, ["--set", "tags", "test", "--walk", test_dir])
    snooze()
    assert result.exit_code == 0

    md = OSXMetaData(dirname / "temp" / "subfolder1" / "sub1.txt")
    assert md.tags == [Tag("test", 0)]

    md = OSXMetaData(dirname / "temp" / "subfolder2")
    assert md.tags == [Tag("test", 0)]


def test_cli_walk_files_only(test_dir):
    """test --walk with --files-only"""

    dirname = pathlib.Path(test_dir)
    os.makedirs(dirname / "temp" / "subfolder1")
    os.makedirs(dirname / "temp" / "subfolder2")
    (dirname / "temp" / "temp1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.txt").touch()

    runner = CliRunner()
    result = runner.invoke(
        cli, ["--set", "tags", "test", "--walk", "--files-only", test_dir]
    )
    snooze()
    assert result.exit_code == 0

    md = OSXMetaData(dirname / "temp" / "subfolder1" / "sub1.txt")
    assert md.tags == [Tag("test", 0)]

    md = OSXMetaData(dirname / "temp" / "subfolder2")
    assert not md.tags


def test_cli_walk_pattern(test_dir):
    """test --walk with --pattern"""

    dirname = pathlib.Path(test_dir)
    os.makedirs(dirname / "temp" / "subfolder1")
    os.makedirs(dirname / "temp" / "subfolder2")
    (dirname / "temp" / "temp1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.pdf").touch()

    runner = CliRunner()
    result = runner.invoke(
        cli, ["--set", "tags", "test", "--walk", "--pattern", "*.pdf", test_dir]
    )
    assert result.exit_code == 0

    md = OSXMetaData(dirname / "temp" / "subfolder1" / "sub1.pdf")
    assert md.tags == [Tag("test", 0)]

    md = OSXMetaData(dirname / "temp" / "subfolder1" / "sub1.txt")
    assert not md.tags

    md = OSXMetaData(dirname / "temp" / "subfolder2")
    assert not md.tags


def test_cli_walk_pattern_2(test_dir):
    """test --walk with more than one --pattern"""

    dirname = pathlib.Path(test_dir)
    os.makedirs(dirname / "temp" / "subfolder1")
    os.makedirs(dirname / "temp" / "subfolder2")
    (dirname / "temp" / "temp1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.pdf").touch()
    (dirname / "temp" / "subfolder2" / "sub2.jpg").touch()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--set",
            "tags",
            "test",
            "--walk",
            "--pattern",
            "*.pdf",
            "--pattern",
            "*.jpg",
            test_dir,
        ],
    )
    assert result.exit_code == 0

    md = OSXMetaData(dirname / "temp" / "subfolder1" / "sub1.pdf")
    assert md.tags == [Tag("test", 0)]

    md = OSXMetaData(dirname / "temp" / "subfolder2" / "sub2.jpg")
    assert md.tags == [Tag("test", 0)]

    md = OSXMetaData(dirname / "temp" / "subfolder1" / "sub1.txt")
    assert not md.tags

    md = OSXMetaData(dirname / "temp" / "subfolder2")
    assert not md.tags


def test_cli_files_only(test_dir):
    """test --files-only without --walk"""

    dirname = pathlib.Path(test_dir)
    os.makedirs(dirname / "temp" / "subfolder1")
    os.makedirs(dirname / "temp" / "subfolder2")
    (dirname / "temp" / "temp1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.txt").touch()

    files = glob.glob(str(dirname / "temp" / "*"))

    runner = CliRunner()
    result = runner.invoke(cli, ["--set", "tags", "test", "--files-only", *files])
    assert result.exit_code == 0

    md = OSXMetaData(dirname / "temp" / "temp1.txt")
    assert md.tags == [Tag("test", 0)]

    md = OSXMetaData(dirname / "temp" / "subfolder1")
    assert not md.tags

    md = OSXMetaData(dirname / "temp" / "subfolder1" / "sub1.txt")
    assert not md.tags


def test_cli_backup_restore(test_dir):
    """Test --backup and --restore"""

    dirname = pathlib.Path(test_dir)
    test_file = dirname / "test_file.txt"
    test_file.touch()

    md = OSXMetaData(test_file)
    md.tags = [Tag("test", 0)]
    md.authors = ["John Doe", "Jane Doe"]
    md.wherefroms = ["http://www.apple.com"]
    md.downloadeddate = [datetime.datetime(2019, 1, 1, 0, 0, 0)]
    md.stationerypad = True

    runner = CliRunner()
    result = runner.invoke(cli, ["--backup", test_file.as_posix()])
    assert result.exit_code == 0

    # test the backup file was written and is readable
    backup_file = dirname / BACKUP_FILENAME
    assert backup_file.is_file()
    backup_data = load_backup_file(backup_file)
    assert backup_data[test_file.name]["stationerypad"] == True

    # wipe the data
    result = runner.invoke(cli, ["--wipe", test_file.as_posix()])
    snooze(LONG_SNOOZE)
    md = OSXMetaData(test_file)
    assert not md.tags
    assert not md.authors
    assert not md.stationerypad

    # restore the data
    result = runner.invoke(cli, ["--restore", test_file.as_posix()])
    snooze(LONG_SNOOZE)
    assert result.exit_code == 0
    assert md.tags == [Tag("test", 0)]
    assert md.authors == ["John Doe", "Jane Doe"]
    assert md.wherefroms == ["http://www.apple.com"]
    assert md.downloadeddate == [datetime.datetime(2019, 1, 1, 0, 0, 0)]
    assert md.stationerypad


def test_cli_backup_walk_pattern(test_dir):
    """test --backup --walk with --pattern"""

    dirname = pathlib.Path(test_dir)
    os.makedirs(dirname / "temp" / "subfolder1")
    os.makedirs(dirname / "temp" / "subfolder2")
    (dirname / "temp" / "temp1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.pdf").touch()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--set", "tags", "test", "--walk", "--pattern", "*.pdf", "--backup", test_dir],
    )
    assert result.exit_code == 0

    md = OSXMetaData(dirname / "temp" / "subfolder1" / "sub1.pdf")
    assert md.tags == [Tag("test", 0)]

    backup_file = dirname / "temp" / "subfolder1" / BACKUP_FILENAME
    assert backup_file.is_file()
    backup_data = load_backup_file(backup_file)
    assert backup_data["sub1.pdf"][_kMDItemUserTags] == [["test", 0]]
    assert backup_data.get("sub1.txt") is None


def test_cli_order(test_dir):
    """Test order CLI options are executed

    Order of execution should be:
    restore, wipe, copyfrom, clear, set, append, remove, mirror, get, list, backup
    """

    dirname = pathlib.Path(test_dir)
    test_file = dirname / "test_file.txt"
    test_file.touch()
    test_file.write_text("test")

    md = OSXMetaData(test_file)
    md.tags = [Tag("test", 0)]
    md.authors = ["John Doe", "Jane Doe"]
    md.wherefroms = ["http://www.apple.com"]
    md.downloadeddate = [datetime.datetime(2019, 1, 1, 0, 0, 0)]
    md.findercomment = "Hello World"
    snooze(LONG_SNOOZE)

    runner = CliRunner()

    # first, create backup file for --restore
    runner.invoke(cli, ["--backup", test_file.as_posix()])

    # wipe the data
    runner.invoke(cli, ["--wipe", test_file.as_posix()])
    snooze(LONG_SNOOZE)

    # restore the data and check order of operations
    result = runner.invoke(
        cli,
        [
            "--get",
            "comment",
            "--set",
            "authors",
            "John Smith",
            "--restore",
            "--set",
            "title",
            "Test Title",
            "--clear",
            "title",
            "--append",
            "tags",
            "test2",
            "--set",
            "comment",
            "foo",
            "--remove",
            "authors",
            "Jane Doe",
            "--append",
            "authors",
            "Jane Smith",
            "--mirror",
            "comment",
            "findercomment",
            test_file.as_posix(),
        ],
    )
    output = parse_cli_output(result.output)
    assert output["comment"] == "Hello World"

    snooze(LONG_SNOOZE)
    md = OSXMetaData(test_file)
    assert md.authors == ["John Smith", "Jane Smith"]
    assert md.findercomment == "Hello World"
    assert md.tags == [Tag("test", 0), Tag("test2", 0)]
