from collections import namedtuple
import datetime

from .constants import *
from .classes import _AttributeList, _AttributeTagsSet

# Information about metadata attributes that can be set
# Each attribute type needs an Attribute namedtuple entry in ATTRIBUTES dict
# To add new entries, create an Attribute namedtuple and create an entry in
# ATTRIBUTES dict where key is short name for the attribute
# Fields in the Attribute namedtuple are:
# name: short name of the attribute -- will also be used as attribute/property
#   in the OSXMetaData class
# constant: the name of the constant for the attribute
#   (e.g. com.apple.metadata:kMDItemCreator)
#   See https://developer.apple.com/documentation/coreservices/file_metadata/mditem?language=objc
#   for reference on common metadata attributes
# type_: expected type for the attribute, e.g. if Apple says it's a CFString, it'll be python str
#   CFNumber = python float, etc.
#   (called type_ so pylint doesn't complain about misplaced type identifier)
# list: (boolean) True if attribute is a list (e.g. a CFArray)
# as_list: (boolean) True if attribute is a single value but stored in a list
#   Note: the only attribute I've seen this on is com.apple.metadata:kMDItemDownloadedDate
# class: the attribute class to use, e.g. _AttributeList or str
# Note: also add short name to __slots__ in __init__.py OSXMetaData
# Note: also add the constant name (e.g. kMDItemDateAdded) to constants.py


Attribute = namedtuple(
    "Attribute", ["name", "constant", "type_", "list", "as_list", "class_"]
)

ATTRIBUTES = {
    "authors": Attribute("authors", kMDItemAuthors, str, True, False, _AttributeList),
    "comment": Attribute("comment", kMDItemComment, str, False, False, str),
    "copyright": Attribute("copyright", kMDItemCopyright, str, False, False, str),
    "creator": Attribute("creator", kMDItemCreator, str, False, False, str),
    "description": Attribute("description", kMDItemDescription, str, False, False, str),
    "downloadeddate": Attribute(
        "downloadeddate",
        kMDItemDownloadedDate,
        datetime.datetime,
        # False,
        True,
        # True,
        False,
        _AttributeList,
    ),
    "findercomment": Attribute(
        "findercomment", kMDItemFinderComment, str, False, False, str
    ),
    "headline": Attribute("headline", kMDItemHeadline, str, False, False, str),
    "keywords": Attribute(
        "keywords", kMDItemKeywords, str, True, False, _AttributeList
    ),
    "tags": Attribute("tags", _kMDItemUserTags, str, True, False, _AttributeTagsSet),
    "wherefroms": Attribute(
        "wherefroms", kMDItemWhereFroms, str, True, False, _AttributeList
    ),
    # "test": Attribute(
    #     "test",
    #     "com.osxmetadata.test:DontTryThisAtHomeKids",
    #     datetime.datetime,
    #     True,
    #     False,
    #     _AttributeList,
    # ),
    # "test_float": Attribute(
    #     "test_float",
    #     "com.osxmetadata.test:DontTryThisAtHomeKids",
    #     float,
    #     False,
    #     False,
    #     float,
    # ),
    # "test_str": Attribute(
    #     "test_str", "com.osxmetadata.test:String", str, False, False, str
    # ),
}

# used for formatting output of --list
_SHORT_NAME_WIDTH = max([len(x) for x in ATTRIBUTES.keys()]) + 5
_LONG_NAME_WIDTH = max([len(x.constant) for x in ATTRIBUTES.values()]) + 10
_CONSTANT_WIDTH = 21 + 5  # currently longest is kMDItemDownloadedDate

# also add entries for attributes by constant and short constant
# do this after computing widths above
_temp_attributes = {}
for attribute in ATTRIBUTES.values():
    if attribute.constant not in ATTRIBUTES:
        _temp_attributes[attribute.constant] = attribute
        constant_name = attribute.constant.split(":", 2)[1]
        _temp_attributes[constant_name] = attribute
    else:
        raise ValueError(f"Duplicate attribute in ATTRIBUTES: {attribute}")
if _temp_attributes:
    ATTRIBUTES.update(_temp_attributes)

# list of all attributes for help text
ATTRIBUTES_LIST = [
    f"{'Short Name':{_SHORT_NAME_WIDTH}} {'Constant':{_CONSTANT_WIDTH}} Long Name"
]
ATTRIBUTES_LIST.extend(
    [
        f"{a.name:{_SHORT_NAME_WIDTH}} "
        f"{a.constant.split(':',2)[1]:{_CONSTANT_WIDTH}} "
        f"{a.constant}"
        for a in [
            ATTRIBUTES[a]
            for a in set([attribute.name for attribute in ATTRIBUTES.values()])
        ]
    ]
)
