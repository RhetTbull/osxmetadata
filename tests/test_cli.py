""" Test osxmetadata command line interface """

import datetime
import glob
import os
import pathlib

import pytest
from click.testing import CliRunner

from osxmetadata import *
from osxmetadata import __version__
from osxmetadata.__main__ import BACKUP_FILENAME, cli
from osxmetadata.backup import load_backup_file

help = """
  -v, --version                   Show the version and exit.
  -w, --walk                      Walk directory tree, processing each file in
                                  the tree.
  -j, --json                      Print output in JSON format, for use with
                                  --list and --get.
  -X, --wipe                      Wipe all metadata attributes from FILE.
  -s, --set ATTRIBUTE VALUE       Set ATTRIBUTE to VALUE.
  -l, --list                      List all metadata attributes for FILE.
  -c, --clear ATTRIBUTE           Remove attribute from FILE.
  -a, --append ATTRIBUTE VALUE    Append VALUE to ATTRIBUTE; for multi-valued
                                  attributes, appends only if VALUE is not
                                  already present.
  -g, --get ATTRIBUTE             Get value of ATTRIBUTE.
  -r, --remove ATTRIBUTE VALUE    Remove VALUE from ATTRIBUTE; only applies to
                                  multi-valued attributes.
  -m, --mirror ATTRIBUTE1 ATTRIBUTE2
                                  Mirror values between ATTRIBUTE1 and
                                  ATTRIBUTE2 so that ATTRIBUTE1 = ATTRIBUTE2;
                                  for multi-valued attributes, merges values;
                                  for string attributes, sets ATTRIBUTE1 =
                                  ATTRIBUTE2 overwriting any value in
                                  ATTRIBUTE1.  For example: '--mirror keywords
                                  tags' sets tags and keywords to same values.
  -B, --backup                    Backup FILE attributes.  Backup file
                                  '.osxmetadata.json' will be created in same
                                  folder as FILE. Only backs up attributes
                                  known to osxmetadata unless used with --all.
  -R, --restore                   Restore FILE attributes from backup file.
                                  Restore will look for backup file
                                  '.osxmetadata.json' in same folder as FILE.
                                  Only restores attributes known to
                                  osxmetadata unless used with --all.
  -V, --verbose                   Print verbose output.
  -f, --copyfrom SOURCE_FILE      Copy attributes from file SOURCE_FILE (only
                                  updates destination attributes that are not
                                  null in SOURCE_FILE).
  --files-only                    Do not apply metadata commands to
                                  directories themselves, only files in a
                                  directory.
  -p, --pattern PATTERN           Only process files matching PATTERN; only
                                  applies to --walk. If specified, only files
                                  matching PATTERN will be processed as each
                                  directory is walked. May be used for than
                                  once to specify multiple patterns. For
                                  example, tag all *.pdf files in projectdir
                                  and subfolders with tag 'project':
                                  osxmetadata --append tags 'project' --walk
                                  projectdir/ --pattern '*.pdf'
  --help                          Show this message and exit.
"""


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

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--wipe", test_file.name],
    )
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
    assert result.exit_code == 0
    md = OSXMetaData(test_file.name)
    assert md.authors == ["John Doe"]
    assert md.tags == [Tag("test", 0)]
    assert md.description == "Goodbye World"


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

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--remove",
            "authors",
            "John Doe",
            "--remove",
            "tags",
            "test,0",
            test_file.name,
        ],
    )
    assert result.exit_code == 0
    assert md.authors == ["Jane Doe"]
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
    assert result.exit_code == 0
    assert "Mirroring" in result.stdout
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
    assert result.exit_code == 0

    md2 = OSXMetaData(test_file2.name)
    assert md2.description == "This is a test file"


def test_cli_walk(test_dir):
    """test --walk"""

    dirname = pathlib.Path(test_dir)
    os.makedirs(dirname / "temp" / "subfolder1")
    os.makedirs(dirname / "temp" / "subfolder2")
    (dirname / "temp" / "temp1.txt").touch()
    (dirname / "temp" / "subfolder1" / "sub1.txt").touch()

    runner = CliRunner()
    result = runner.invoke(cli, ["--set", "tags", "test", "--walk", test_dir])
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


def test_cli_backup_restore(test_dir, snooze):
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
    snooze()
    md = OSXMetaData(test_file)
    assert not md.tags
    assert not md.authors
    assert not md.stationerypad

    # restore the data
    result = runner.invoke(cli, ["--restore", test_file.as_posix()])
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


def test_cli_order(test_dir, snooze):
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

    runner = CliRunner()

    # first, create backup file for --restore
    runner.invoke(cli, ["--backup", test_file.as_posix()])

    # wipe the data
    runner.invoke(cli, ["--wipe", test_file.as_posix()])
    snooze()

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

    snooze()
    md = OSXMetaData(test_file)
    assert md.authors == ["John Smith", "Jane Smith"]
    assert md.findercomment == "Hello World"
    assert md.tags == [Tag("test", 0), Tag("test2", 0)]
