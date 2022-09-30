"""Test osxmetadata basic mditem metadata tags"""

import os
import time
from tempfile import NamedTemporaryFile

import pytest

from osxmetadata import OSXMetaData
from osxmetadata.attribute_data import (
    MDITEM_ATTRIBUTE_AUDIO,
    MDITEM_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_IMAGE,
    MDITEM_ATTRIBUTE_READ_ONLY,
    MDITEM_ATTRIBUTE_VIDEO,
)

from .conftest import value_for_type

# filter out the read-only attributes
MDITEM_ATTRIBUTES_TO_TEST = [
    a["name"]
    for a in MDITEM_ATTRIBUTE_DATA.values()
    if a["name"] not in MDITEM_ATTRIBUTE_READ_ONLY
    and a["name"] not in MDITEM_ATTRIBUTE_AUDIO
    and a["name"] not in MDITEM_ATTRIBUTE_IMAGE
    and a["name"] not in MDITEM_ATTRIBUTE_VIDEO
]


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTES_TO_TEST)
def test_mditem_attributes_get_set(attribute_name):
    """test mditem attributes"""

    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with NamedTemporaryFile(dir=os.getcwd(), prefix="tmp_") as test_file:
        attribute = MDITEM_ATTRIBUTE_DATA[attribute_name]
        attribute_type = attribute["python_type"]
        test_value = value_for_type(attribute_type)

        md = OSXMetaData(test_file.name)
        md.set(attribute_name, test_value)
        if attribute_name == "kMDItemFinderComment":
            time.sleep(0.1)  # Finder comment is slow to update
        assert md.get(attribute_name) == test_value


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTES_TO_TEST)
def test_mditem_attributes_dict(attribute_name):
    """test mditem attributes with dict access"""

    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with NamedTemporaryFile(dir=os.getcwd(), prefix="tmp_") as test_file:
        attribute = MDITEM_ATTRIBUTE_DATA[attribute_name]
        attribute_type = attribute["python_type"]
        test_value = value_for_type(attribute_type)

        md = OSXMetaData(test_file.name)
        md[attribute_name] = test_value
        if attribute_name == "kMDItemFinderComment":
            time.sleep(0.1)  # Finder comment is slow to update
        assert md[attribute_name] == test_value


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTES_TO_TEST)
def test_mditem_attributes_property(attribute_name):
    """test mditem attributes with property access"""

    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with NamedTemporaryFile(dir=os.getcwd(), prefix="tmp_") as test_file:
        attribute = MDITEM_ATTRIBUTE_DATA[attribute_name]
        attribute_type = attribute["python_type"]
        test_value = value_for_type(attribute_type)

        md = OSXMetaData(test_file.name)
        setattr(md, attribute_name, test_value)
        if attribute_name == "kMDItemFinderComment":
            time.sleep(0.1)  # Finder comment is slow to update
        assert getattr(md, attribute_name) == test_value


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTES_TO_TEST)
def test_mditem_attributes_short_name(attribute_name):
    """test mditem attributes"""

    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with NamedTemporaryFile(dir=os.getcwd(), prefix="tmp_") as test_file:
        attribute = MDITEM_ATTRIBUTE_DATA[attribute_name]
        attribute_type = attribute["python_type"]
        test_value = value_for_type(attribute_type)

        md = OSXMetaData(test_file.name)
        setattr(md, attribute["short_name"], test_value)
        if attribute_name == "findercomment":
            time.sleep(0.1)  # Finder comment is slow to update
        assert getattr(md, attribute["short_name"]) == test_value


@pytest.mark.parametrize("attribute_name", MDITEM_ATTRIBUTE_DATA.keys())
def test_mditem_attributes_all(attribute_name):
    """Test that all attributes can be accessed without error"""

    # can't use tmp_path fixture because the tmpfs filesystem doesn't support xattrs
    with NamedTemporaryFile(dir=os.getcwd(), prefix="tmp_") as test_file:
        md = OSXMetaData(test_file.name)
        md.get(attribute_name)


def test_mditem_attributes_image(test_image):
    """test mditem attributes for image files"""

    md = OSXMetaData(test_image)
    assert md.get("kMDItemLatitude") == "-34.91889166666667"
    assert md.get("kMDItemPixelHeight") == 2754


def test_mditem_attributes_video(test_video):
    """test mditem attributes for video files"""

    md = OSXMetaData(test_video)
    assert sorted(md.get("kMDItemCodecs")) == sorted(["H.264", "AAC", "Timed Metadata"])
    assert md.get("kMDItemAudioBitRate") == 64.0


def test_mditem_attributes_audio(test_audio):
    """test mditem attributes for audio files"""

    md = OSXMetaData(test_audio)
    assert md.get("kMDItemAudioSampleRate") == 44100.0
