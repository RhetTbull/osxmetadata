from collections import namedtuple
import datetime

from .constants import *
from .classes import _AttributeList, _AttributeTagsList

# Information about metadata attributes that can be set
# Each attribute type needs an Attribute namedtuple entry in ATTRIBUTES dict
# To add new entries, create an Attribute namedtuple and create an entry in
# ATTRIBUTES dict where key is short name for the attribute
# Fields in the Attribute namedtuple are:
# name: short name of the attribute -- will also be used as attribute/property
#   in the OSXMetaData class
# short_constant: the short constant name for the attribute
#   (e.g. kMDItemFinderComment)
# constant: the long name of the constant for the attribute
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
# help: help text for the attribute (for use in command line interface)
# Note: also add short name to __slots__ in __init__.py OSXMetaData
# Note: also add the constant name (e.g. kMDItemDateAdded) to constants.py


Attribute = namedtuple(
    "Attribute",
    [
        "name",
        "short_constant",
        "constant",
        "type_",
        "list",
        "as_list",
        "class_",
        "help",
    ],
)

ATTRIBUTES = {
    "authors": Attribute(
        "authors",
        "kMDItemAuthors",
        kMDItemAuthors,
        str,
        True,
        False,
        _AttributeList,
        "The author, or authors, of the contents of the file.  A list of strings.",
    ),
    "comment": Attribute(
        "comment",
        "kMDItemComment",
        kMDItemComment,
        str,
        False,
        False,
        str,
        "A comment related to the file.  This differs from the Finder comment, "
        + "kMDItemFinderComment.  A string.",
    ),
    "copyright": Attribute(
        "copyright",
        "kMDItemCopyright",
        kMDItemCopyright,
        str,
        False,
        False,
        str,
        "The copyright owner of the file contents.  A string.",
    ),
    "creator": Attribute(
        "creator",
        "kMDItemCreator",
        kMDItemCreator,
        str,
        False,
        False,
        str,
        "Application used to create the document content (for example “Word”, “Pages”, "
        + "and so on).  A string.",
    ),
    "description": Attribute(
        "description",
        "kMDItemDescription",
        kMDItemDescription,
        str,
        False,
        False,
        str,
        "A description of the content of the resource.  The description may include an abstract, "
        + "table of contents, reference to a graphical representation of content or a "
        + "free-text account of the content.  A string.",
    ),
    "downloadeddate": Attribute(
        "downloadeddate",
        "kMDItemDownloadedDate",
        kMDItemDownloadedDate,
        datetime.datetime,
        # False,
        True,
        # True,
        False,
        _AttributeList,
        "The date the item was downloaded.  A date in ISO 8601 format: e.g. "
        + "2000-01-12T12:00:00 or 2000-12-31 (ISO 8601 w/o time zone)",
    ),
    "findercomment": Attribute(
        "findercomment",
        "kMDItemFinderComment",
        kMDItemFinderComment,
        str,
        False,
        False,
        str,
        "Finder comments for this file.  A string.",
    ),
    "headline": Attribute(
        "headline",
        "kMDItemHeadline",
        kMDItemHeadline,
        str,
        False,
        False,
        str,
        "A publishable entry providing a synopsis of the contents of the file.  A string.",
    ),
    "keywords": Attribute(
        "keywords",
        "kMDItemKeywords",
        kMDItemKeywords,
        str,
        True,
        False,
        _AttributeList,
        "Keywords associated with this file. For example, “Birthday”, “Important”, etc. "
        + "This differs from Finder tags (_kMDItemUserTags) which are keywords/tags shown "
        + 'in the Finder and searchable in Spotlight using "tag:tag_name".  '
        + "A list of strings.",
    ),
    "tags": Attribute(
        "tags",
        "_kMDItemUserTags",
        _kMDItemUserTags,
        str,
        True,
        False,
        _AttributeTagsList,
        'Finder tags; searchable in Spotlight using "tag:tag_name".  '
        + "If you want tags/keywords visible in the Finder, use this instead of kMDItemKeywords.  "
        + "A list of strings.",
    ),
    "wherefroms": Attribute(
        "wherefroms",
        "kMDItemWhereFroms",
        kMDItemWhereFroms,
        str,
        True,
        False,
        _AttributeList,
        "Describes where the file was obtained from (e.g. URL downloaded from).  "
        + "A list of strings.",
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
        _temp_attributes[attribute.short_constant] = attribute
    else:
        raise ValueError(f"Duplicate attribute in ATTRIBUTES: {attribute}")
if _temp_attributes:
    ATTRIBUTES.update(_temp_attributes)

# list of all attributes for help text
# ATTRIBUTES_LIST = [
#     f"{'Short Name':{_SHORT_NAME_WIDTH}} {'Constant':{_CONSTANT_WIDTH}} Long Name"
# ]
# ATTRIBUTES_LIST.extend(
#     sorted(
#         [
#             f"{a.name:{_SHORT_NAME_WIDTH}} "
#             f"{a.constant.split(':',2)[1]:{_CONSTANT_WIDTH}} "
#             f"{a.constant}"
#             for a in [
#                 ATTRIBUTES[a]
#                 for a in set([attribute.name for attribute in ATTRIBUTES.values()])
#             ]
#         ]
#     )
# )
