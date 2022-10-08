""" Python package to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """

from ._version import __version__
from .attribute_data import (
    MDIMPORTER_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_READ_ONLY,
    MDITEM_ATTRIBUTE_SHORT_NAMES,
    NSURL_RESOURCE_KEY_DATA,
)
from .constants import (
    FINDER_COLOR_BLUE,
    FINDER_COLOR_GRAY,
    FINDER_COLOR_GREEN,
    FINDER_COLOR_NONE,
    FINDER_COLOR_ORANGE,
    FINDER_COLOR_PURPLE,
    FINDER_COLOR_RED,
    FINDER_COLOR_YELLOW,
)
from .finder_info import _kFinderColor, _kFinderInfo, _kFinderStationeryPad
from .finder_tags import Tag, _kMDItemUserTags
from .mditem import MDItemValueType
from .osxmetadata import ALL_ATTRIBUTES, ASDICT_ATTRIBUTES, OSXMetaData

# add metadata attribute constants such as kMDItemFinderComment and NSURLTagNamesKey to module namespace
for constant in MDITEM_ATTRIBUTE_DATA.keys():
    globals()[constant] = constant
for constant in MDIMPORTER_ATTRIBUTE_DATA.keys():
    globals()[constant] = constant
for constant in NSURL_RESOURCE_KEY_DATA.keys():
    globals()[constant] = constant


__all__ = [
    "ALL_ATTRIBUTES",
    "ASDICT_ATTRIBUTES",
    "FINDER_COLOR_BLUE",
    "FINDER_COLOR_GRAY",
    "FINDER_COLOR_GREEN",
    "FINDER_COLOR_NONE",
    "FINDER_COLOR_ORANGE",
    "FINDER_COLOR_PURPLE",
    "FINDER_COLOR_RED",
    "FINDER_COLOR_YELLOW",
    "MDIMPORTER_ATTRIBUTE_DATA",
    "MDITEM_ATTRIBUTE_DATA",
    "MDITEM_ATTRIBUTE_READ_ONLY",
    "MDITEM_ATTRIBUTE_SHORT_NAMES",
    "MDItemValueType",
    "NSURL_RESOURCE_KEY_DATA",
    "OSXMetaData",
    "Tag",
    "__version__",
    "_kFinderColor",
    "_kFinderInfo",
    "_kFinderStationeryPad",
    "_kMDItemUserTags",
    *MDIMPORTER_ATTRIBUTE_DATA.keys(),
    *MDITEM_ATTRIBUTE_DATA.keys(),
    *NSURL_RESOURCE_KEY_DATA.keys(),
]
