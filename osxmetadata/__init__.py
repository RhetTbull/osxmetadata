""" Python package to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """

from ._version import __version__
from .attribute_data import MDITEM_ATTRIBUTE_DATA, NSURL_RESOURCE_KEY_DATA
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
from .finder_tags import Tag, _kMDItemUserTags
from .mditem import MDItemValueType
from .osxmetadata import OSXMetaData

# add metadata attribute constants such as kMDItemFinderComment and NSURLTagNamesKey to module namespace
for constant in MDITEM_ATTRIBUTE_DATA.keys():
    globals()[constant] = constant
for constant in NSURL_RESOURCE_KEY_DATA.keys():
    globals()[constant] = constant


__all__ = [
    "FINDER_COLOR_BLUE",
    "FINDER_COLOR_GRAY",
    "FINDER_COLOR_GREEN",
    "FINDER_COLOR_NONE",
    "FINDER_COLOR_ORANGE",
    "FINDER_COLOR_PURPLE",
    "FINDER_COLOR_RED",
    "FINDER_COLOR_YELLOW",
    "MDItemValueType",
    "OSXMetaData",
    "Tag",
    "__version__",
    "_kMDItemUserTags",
    *MDITEM_ATTRIBUTE_DATA.keys(),
    *NSURL_RESOURCE_KEY_DATA.keys(),
]


#     FinderInfo,
#     _COLORIDS,
#     _COLORNAMES,
#     _FINDER_COMMENT_NAMES,
#     _MAX_FINDERCOMMENT,
#     _MAX_WHEREFROM,
#     _VALID_COLORIDS,
#     _kMDItemUserTags,
# )
# from .debug import _debug, _set_debug
