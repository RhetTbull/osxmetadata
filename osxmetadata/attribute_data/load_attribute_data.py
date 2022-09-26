"""Load attribute metadata from JSON files"""

import datetime
import json
import pathlib
import typing as t

import Foundation

METADATA_FILES = [
    "audio_attributes.json",
    "common_attributes.json",
    "filesystem_attributes.json",
    "image_attributes.json",
    "video_attributes.json",
]

RESOURCE_KEY_FILES = ["nsurl_resource_keys.json"]


def load_attribute_data() -> t.Dict:
    """Load attribute metadata from JSON files"""
    # TODO: would be better to use importlib.abc.ResourceReader but I can't find a single example of how to do this
    parent = pathlib.Path(__file__).parent
    data = {}
    for filename in METADATA_FILES:
        with open(parent / filename, "r") as f:
            file_data = json.load(f)
            for item in file_data:
                data[item["name"]] = item

    # add python types (e.g. CFString -> str)
    # the types used in the JSON files are the CF types with these counts
    # {'CFArray of CFStrings': 26, 'CFString': 61, 'CFNumber': 35, 'CFBoolean': 8, 'CFDate': 8}
    for key, value in data.items():
        if value["type"] == "CFString":
            data[key]["python_type"] = str
        elif value["type"] == "CFNumber":
            data[key]["python_type"] = float
        elif value["type"] == "CFBoolean":
            data[key]["python_type"] = bool
        elif value["type"] == "CFDate":
            data[key]["python_type"] = datetime.datetime
        elif value["type"] == "CFArray of CFStrings":
            data[key]["python_type"] = list
        else:
            raise ValueError(f"Unknown type {value['type']}")

    # add the attribute short_name which is lowercase of the part after kMDItem
    for key, value in data.items():
        if value["name"].startswith("kMDItem"):
            data[key]["short_name"] = value["name"][7:].lower()
        else:
            data[key]["short_name"] = value["name"].lower()

    # add the xattr_constant which is com.apple.metadata:MDItemName
    for key, value in data.items():
        data[key]["xattr_constant"] = f"com.apple.metadata:{value['name']}"

    return data


def load_resource_key_data() -> t.Dict:
    """Load resource key metadata from JSON files"""
    # TODO: would be better to use importlib.abc.ResourceReader but I can't find a single example of how to do this
    parent = pathlib.Path(__file__).parent
    data = {}
    for filename in RESOURCE_KEY_FILES:
        with open(parent / filename, "r") as f:
            file_data = json.load(f)
            for item in file_data:
                # Some resource keys only available on certain versions of macOS
                try:
                    getattr(Foundation, item["name"])
                except AttributeError:
                    # Not available on this version of macOS
                    continue
                data[item["name"]] = item
    return data


ATTRIBUTE_DATA = load_attribute_data()
ATTRIBUTE_SHORT_NAMES = {
    item["short_name"]: item["name"] for item in ATTRIBUTE_DATA.values()
}
RESOURCE_KEY_DATA = load_resource_key_data()

__all__ = [
    "ATTRIBUTE_DATA",
    "ATTRIBUTE_SHORT_NAMES",
    "RESOURCE_KEY_DATA",
]
