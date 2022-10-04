"""Load attribute metadata from JSON files"""

import datetime
import json
import pathlib
import typing as t

import Foundation

MDITEM_METADATA_FILES = [
    "audio_attributes.json",
    "common_attributes.json",
    "filesystem_attributes.json",
    "image_attributes.json",
    "video_attributes.json",
]

NSURL_RESOURCE_KEY_FILES = ["nsurl_resource_keys.json"]

MDIMPORTER_CONSTANT_FILES = ["mdimporter_constants.json"]


def load_mditem_attribute_data(files) -> t.Dict:
    """Load attribute metadata from JSON files"""
    # TODO: would be better to use importlib.abc.ResourceReader but I can't find a single example of how to do this
    parent = pathlib.Path(__file__).parent
    data = {}
    for filename in files:
        with open(parent / filename, "r") as f:
            file_data = json.load(f)
            for item in file_data:
                data[item["name"]] = item

    # add python types (e.g. CFString -> str) and help text types
    # the types used in the JSON files are the CF types with these counts
    # {'CFArray of CFStrings': 26, 'CFString': 61, 'CFNumber': 35, 'CFBoolean': 8, 'CFDate': 8}
    for key, value in data.items():
        if value["type"] == "CFString":
            data[key]["python_type"] = "str"
            data[key]["help_type"] = "string"
        elif value["type"] == "CFNumber":
            data[key]["python_type"] = "float"
            data[key]["help_type"] = "number"
        elif value["type"] == "CFBoolean":
            data[key]["python_type"] = "bool"
            data[key]["help_type"] = "boolean"
        elif value["type"] == "CFDate":
            data[key]["python_type"] = "datetime.datetime"
            data[key]["help_type"] = "date/time"
        elif value["type"] == "CFArray of CFStrings":
            data[key]["python_type"] = "list"
            data[key]["help_type"] = "list of strings"
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


def load_nsurl_resource_key_data() -> t.Dict:
    """Load NSRL resource key metadata from JSON files"""
    # TODO: would be better to use importlib.abc.ResourceReader but I can't find a single example of how to do this
    parent = pathlib.Path(__file__).parent
    data = {}
    for filename in NSURL_RESOURCE_KEY_FILES:
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


def load_mdimporter_constant_data() -> t.Dict:
    """Load MDImporter constants from JSON files"""
    parent = pathlib.Path(__file__).parent
    data = {}
    for filename in MDIMPORTER_CONSTANT_FILES:
        with open(parent / filename, "r") as f:
            file_data = json.load(f)
            for item in file_data:
                data[item["name"]] = item
    return data


# all attribute data
MDITEM_ATTRIBUTE_DATA = load_mditem_attribute_data(MDITEM_METADATA_FILES)


# Add kMDItemDownloadedDate which isn't in the normal MDItem reference but is
# referenced in the MDImporter reference here:
# https://developer.apple.com/documentation/coreservices/kmditemdownloadeddate?language=objc
MDITEM_ATTRIBUTE_DATA["kMDItemDownloadedDate"] = {
    "name": "kMDItemDownloadedDate",
    "description": "Date the item was downloaded.",
    "version": "10.7",
    "type": "CFArray of CFDates",
    "python_type": "list[datetime.datetime]",
    "help_type": "list of date/time",
    "short_name": "downloadeddate",
    "xattr_constant": "com.apple.metadata:kMDItemDownloadedDate",
}

# specific types of attribute data
MDITEM_ATTRIBUTE_AUDIO = load_mditem_attribute_data(["audio_attributes.json"])
MDITEM_ATTRIBUTE_COMMON = load_mditem_attribute_data(["common_attributes.json"])
MDITEM_ATTRIBUTE_FILESYSTEM = load_mditem_attribute_data(["filesystem_attributes.json"])
MDITEM_ATTRIBUTE_IMAGE = load_mditem_attribute_data(["image_attributes.json"])
MDITEM_ATTRIBUTE_VIDEO = load_mditem_attribute_data(["video_attributes.json"])

# short names for accessing via OSXMetaData().short_name
MDITEM_ATTRIBUTE_SHORT_NAMES = {
    item["short_name"]: item["name"] for item in MDITEM_ATTRIBUTE_DATA.values()
}

# Some MDItem attributes are read-only
MDITEM_ATTRIBUTE_READ_ONLY = {
    "kMDItemAttributeChangeDate",
    "kMDItemContentType",
    "kMDItemKind",
    "kMDItemLastUsedDate",
    "kMDItemSecurityMethod",
    "kMDItemTextContent",
    "kMDItemFSHasCustomIcon",
    "kMDItemFSIsStationery",
    "kMDItemDisplayName",
    "kMDItemFSContentChangeDate",
    "kMDItemFSCreationDate",
    "kMDItemFSInvisible",
    "kMDItemFSIsExtensionHidden",
    "kMDItemFSLabel",
    "kMDItemFSName",
    "kMDItemFSNodeCount",
    "kMDItemFSOwnerGroupID",
    "kMDItemFSOwnerUserID",
    "kMDItemFSSize",
    "kMDItemPath",
}

NSURL_RESOURCE_KEY_DATA = load_nsurl_resource_key_data()

MDIMPORTER_ATTRIBUTE_DATA = load_mdimporter_constant_data()


__all__ = [
    "MDITEM_ATTRIBUTE_DATA",
    "MDITEM_ATTRIBUTE_READ_ONLY",
    "MDITEM_ATTRIBUTE_SHORT_NAMES",
    "MDITEM_ATTRIBUTE_AUDIO",
    "MDITEM_ATTRIBUTE_COMMON",
    "MDITEM_ATTRIBUTE_FILESYSTEM",
    "MDITEM_ATTRIBUTE_IMAGE",
    "MDITEM_ATTRIBUTE_VIDEO",
    "NSURL_RESOURCE_KEY_DATA",
    "MDIMPORTER_ATTRIBUTE_DATA",
]
