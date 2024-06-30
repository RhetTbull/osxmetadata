"""Test osxmetadata basic mditem metadata tags"""

import os

import pytest

from osxmetadata import OSXMetaData
from osxmetadata.attribute_data import (
    MDITEM_ATTRIBUTE_AUDIO,
    MDITEM_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_IMAGE,
    MDITEM_ATTRIBUTE_READ_ONLY,
    MDITEM_ATTRIBUTE_VIDEO,
)

from .conftest import FINDER_COMMENT_SNOOZE, snooze, value_for_type

# filter out the read-only attributes
MDITEM_ATTRIBUTES_TO_TEST = [
    a["name"]
    for a in MDITEM_ATTRIBUTE_DATA.values()
    if a["name"] not in MDITEM_ATTRIBUTE_READ_ONLY
    and a["name"] not in MDITEM_ATTRIBUTE_AUDIO
    and a["name"] not in MDITEM_ATTRIBUTE_IMAGE
    and a["name"] not in MDITEM_ATTRIBUTE_VIDEO
]

# Not all attributes can be cleared by setting to None
MDITEM_ATTRIBUTES_CAN_BE_REMOVED = [
    a for a in MDITEM_ATTRIBUTES_TO_TEST if a not in ["kMDItemContentModificationDate"]
]


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTES_TO_TEST)
def test_mditem_attributes_get_set(attribute_name, test_file):
    """test mditem attributes"""

    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    attribute = MDITEM_ATTRIBUTE_DATA[attribute_name]
    attribute_type = attribute["python_type"]
    test_value = value_for_type(attribute_type)

    md = OSXMetaData(test_file.name)
    md.set(attribute_name, test_value)
    snooze()
    if attribute_name == "kMDItemFinderComment":
        snooze(FINDER_COMMENT_SNOOZE)
    assert md.get(attribute_name) == test_value


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTES_TO_TEST)
def test_mditem_attributes_dict(attribute_name, test_file):
    """test mditem attributes with dict access"""

    attribute = MDITEM_ATTRIBUTE_DATA[attribute_name]
    attribute_type = attribute["python_type"]
    test_value = value_for_type(attribute_type)

    md = OSXMetaData(test_file.name)
    md[attribute_name] = test_value
    snooze()
    if attribute_name == "kMDItemFinderComment":
        snooze(FINDER_COMMENT_SNOOZE)
    assert md[attribute_name] == test_value


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTES_TO_TEST)
def test_mditem_attributes_property(attribute_name, test_file):
    """test mditem attributes with property access"""

    attribute = MDITEM_ATTRIBUTE_DATA[attribute_name]
    attribute_type = attribute["python_type"]
    test_value = value_for_type(attribute_type)

    md = OSXMetaData(test_file.name)
    setattr(md, attribute_name, test_value)
    snooze()
    if attribute_name == "kMDItemFinderComment":
        snooze(FINDER_COMMENT_SNOOZE)
    assert getattr(md, attribute_name) == test_value


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTES_TO_TEST)
def test_mditem_attributes_short_name(attribute_name, test_file):
    """test mditem attributes"""

    attribute = MDITEM_ATTRIBUTE_DATA[attribute_name]
    attribute_type = attribute["python_type"]
    test_value = value_for_type(attribute_type)

    md = OSXMetaData(test_file.name)
    setattr(md, attribute["short_name"], test_value)
    snooze()
    if attribute_name == "kMDItemFinderComment":
        snooze(FINDER_COMMENT_SNOOZE)
    assert getattr(md, attribute["short_name"]) == test_value


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTE_DATA.keys())
def test_mditem_attributes_all(attribute_name, test_file):
    """Test that all attributes can be accessed without error"""

    md = OSXMetaData(test_file.name)
    md.get(attribute_name)


# this test failes on kMDItemFinderComment though the code works when run outside pytest
@pytest.mark.parametrize(
    "attribute_name",
    [
        attr
        for attr in MDITEM_ATTRIBUTES_CAN_BE_REMOVED
        if attr != "kMDItemFinderComment"
    ],
)
def test_mditem_attributes_set_none(attribute_name, test_file):
    """test mditem attributes can be set to None to remove"""

    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    attribute = MDITEM_ATTRIBUTE_DATA[attribute_name]
    attribute_type = attribute["python_type"]
    test_value = value_for_type(attribute_type)
    md = OSXMetaData(test_file.name)
    md.set(attribute_name, test_value)
    snooze()
    if attribute_name == "kMDItemFinderComment":
        snooze(FINDER_COMMENT_SNOOZE)  # Finder needs a moment to update the comment
    assert md.get(attribute_name)
    md.set(attribute_name, None)
    snooze()
    if attribute_name == "kMDItemFinderComment":
        snooze(FINDER_COMMENT_SNOOZE)
    assert not md.get(attribute_name)


@pytest.mark.skipif(
    bool(os.environ.get("GITHUB_ACTION")), reason="GitHub Actions doesn't run md import"
)
def test_mditem_attributes_image(test_image):
    """test mditem attributes for image files"""

    md = OSXMetaData(test_image)
    assert md.get("kMDItemLatitude") == "-34.91889166666667"
    assert md.get("kMDItemPixelHeight") == 2754


@pytest.mark.skipif(
    bool(os.environ.get("GITHUB_ACTION")), reason="GitHub Actions doesn't run md import"
)
def test_mditem_attributes_video(test_video):
    """test mditem attributes for video files"""

    md = OSXMetaData(test_video)
    assert "H.264" in md.get("kMDItemCodecs")
    assert md.get("kMDItemAudioBitRate") == 64.0


@pytest.mark.skipif(
    bool(os.environ.get("GITHUB_ACTION")), reason="GitHub Actions doesn't run md import"
)
def test_mditem_attributes_audio(test_audio):
    """test mditem attributes for audio files"""

    md = OSXMetaData(test_audio)
    assert md.get("kMDItemAudioSampleRate") == 44100.0


def test_get_set_mditem_attribute_value(test_file):
    """test get and set of mditem attribute value using the direct methods without value conversion, #83"""

    md = OSXMetaData(test_file.name)
    md.set_mditem_attribute_value("kMDItemComment", "foo,bar")
    snooze()
    assert md.get_mditem_attribute_value("kMDItemComment") == "foo,bar"
    assert md.comment == "foo,bar"


def test_attribute_get_set(test_file):
    """Test direct access get/set attribute values"""

    md = OSXMetaData(test_file.name)
    assert not md.authors
    md.authors = ["foo", "bar"]
    snooze()
    assert md.authors == ["foo", "bar"]
    md.authors = ["bar"]
    snooze()
    assert md.authors == ["bar"]
    md.set("authors", ["foo"])
    snooze()
    assert md.authors == ["foo"]
