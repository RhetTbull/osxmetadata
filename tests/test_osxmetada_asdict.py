"""Test osxmetadata asdict and to_json method"""

import datetime
import json

from osxmetadata import ASDICT_ATTRIBUTES, OSXMetaData

from .conftest import snooze


def test_asdict(test_file):
    """Test asdict method"""
    md = OSXMetaData(test_file.name)
    md.authors = ["Jane Smith"]
    snooze()
    asdict = md.asdict()
    assert len(asdict) == len(ASDICT_ATTRIBUTES)
    assert asdict["kMDItemAuthors"] == ["Jane Smith"]


def test_asdict_subset(test_file):
    """Test asdict method with subset of attributes"""
    md = OSXMetaData(test_file.name)
    md.authors = ["Jane Smith"]
    snooze()
    asdict = md.asdict(attributes={"kMDItemAuthors"})
    assert len(asdict) == 1
    assert asdict["kMDItemAuthors"] == ["Jane Smith"]


def test_to_json(test_file):
    """Test to_json method"""
    md = OSXMetaData(test_file.name)
    md.authors = ["Jane Smith"]
    md.duedate = datetime.datetime(2022, 10, 1)
    snooze()
    json_str = md.to_json()
    json_data = json.loads(json_str)
    assert json_data["kMDItemAuthors"] == ["Jane Smith"]
    assert json_data["kMDItemDueDate"] == datetime.datetime(2022, 10, 1).isoformat()
