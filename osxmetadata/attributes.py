""" Constants and validation for metadata attributes that can be set """


import datetime
from collections import namedtuple  # pylint: disable=syntax-error

from .classes import (
    _AttributeFinderColor,
    _AttributeFinderInfo,
    _AttributeList,
    _AttributeTagsList,
)
from .constants import *
from .datetime_utils import (
    datetime_has_tz,
    datetime_naive_to_local,
    datetime_remove_tz,
    datetime_tz_to_utc,
)

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
# class_: the attribute class to use, e.g. _AttributeList or str
# append: the attribute can be operated on with append
# update: the attribute can be operated on with update
# help: help text for the attribute (for use in command line interface)
# api_help: help text for use in documentation for the programmer who will use the library
#           if None, will use same text as help
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
        "append",
        "update",
        "help",
        "api_help",
    ],
)

ATTRIBUTES = {
    "authors": Attribute(
        name="authors",
        short_constant="kMDItemAuthors",
        constant=kMDItemAuthors,
        type_=str,
        list=True,
        as_list=False,
        class_=_AttributeList,
        append=True,
        update=True,
        help="The author, or authors, of the contents of the file.  A list of strings.",
        api_help=None,
    ),
    "comment": Attribute(
        name="comment",
        short_constant="kMDItemComment",
        constant=kMDItemComment,
        type_=str,
        list=False,
        as_list=False,
        class_=str,
        append=True,
        update=False,
        help="A comment related to the file.  This differs from the Finder comment, "
        + "kMDItemFinderComment.  A string.",
        api_help=None,
    ),
    "copyright": Attribute(
        name="copyright",
        short_constant="kMDItemCopyright",
        constant=kMDItemCopyright,
        type_=str,
        list=False,
        as_list=False,
        class_=str,
        append=True,
        update=False,
        help="The copyright owner of the file contents.  A string.",
        api_help=None,
    ),
    "creator": Attribute(
        name="creator",
        short_constant="kMDItemCreator",
        constant=kMDItemCreator,
        type_=str,
        list=False,
        as_list=False,
        class_=str,
        append=True,
        update=False,
        help="Application used to create the document content (for example “Word”, “Pages”, "
        + "and so on).  A string.",
        api_help=None,
    ),
    "description": Attribute(
        name="description",
        short_constant="kMDItemDescription",
        constant=kMDItemDescription,
        type_=str,
        list=False,
        as_list=False,
        class_=str,
        append=True,
        update=False,
        help="A description of the content of the resource.  The description may include an abstract, "
        + "table of contents, reference to a graphical representation of content or a "
        + "free-text account of the content.  A string.",
        api_help=None,
    ),
    "downloadeddate": Attribute(
        name="downloadeddate",
        short_constant="kMDItemDownloadedDate",
        constant=kMDItemDownloadedDate,
        type_=datetime.datetime,
        list=True,
        as_list=False,
        class_=_AttributeList,
        append=False,
        update=False,
        help="The date the item was downloaded.  A date in ISO 8601 format, "
        "time and timezone offset are optional: e.g. "
        + "2020-04-14T12:00:00 (ISO 8601 w/o timezone), "
        + "2020-04-14 (ISO 8601 w/o time and time zone), or "
        + "2020-04-14T12:00:00-07:00 (ISO 8601 with timezone offset). "
        + "Times without timezone offset are assumed to be in local timezone.",
        api_help="The date the item was downloaded.  A datetime.datetime object.  "
        + "If datetime.datetime object lacks tzinfo (i.e. it is timezone naive), it "
        + "will be assumed to be in local timezone.",
    ),
    "findercomment": Attribute(
        name="findercomment",
        short_constant="kMDItemFinderComment",
        constant=kMDItemFinderComment,
        type_=str,
        list=False,
        as_list=False,
        class_=str,
        append=True,
        update=False,
        help="Finder comments for this file.  A string.",
        api_help=None,
    ),
    "headline": Attribute(
        name="headline",
        short_constant="kMDItemHeadline",
        constant=kMDItemHeadline,
        type_=str,
        list=False,
        as_list=False,
        class_=str,
        append=True,
        update=False,
        help="A publishable entry providing a synopsis of the contents of the file.  A string.",
        api_help=None,
    ),
    "keywords": Attribute(
        name="keywords",
        short_constant="kMDItemKeywords",
        constant=kMDItemKeywords,
        type_=str,
        list=True,
        as_list=False,
        class_=_AttributeList,
        append=True,
        update=True,
        help="Keywords associated with this file. For example, “Birthday”, “Important”, etc. "
        + "This differs from Finder tags (_kMDItemUserTags) which are keywords/tags shown "
        + 'in the Finder and searchable in Spotlight using "tag:tag_name".  '
        + "A list of strings.",
        api_help=None,
    ),
    "tags": Attribute(
        name="tags",
        short_constant="_kMDItemUserTags",
        constant=_kMDItemUserTags,
        type_=str,
        list=True,
        as_list=False,
        class_=_AttributeTagsList,
        append=True,
        update=True,
        help='Finder tags; searchable in Spotlight using "tag:tag_name".  '
        + "If you want tags/keywords visible in the Finder, use this instead of kMDItemKeywords.  "
        + "A list of Tag objects.",
        api_help=None,
    ),
    "wherefroms": Attribute(
        name="wherefroms",
        short_constant="kMDItemWhereFroms",
        constant=kMDItemWhereFroms,
        type_=str,
        list=True,
        as_list=False,
        class_=_AttributeList,
        append=True,
        update=True,
        help="Describes where the file was obtained from (e.g. URL downloaded from).  "
        + "A list of strings.",
        api_help=None,
    ),
    "finderinfo": Attribute(
        name="finderinfo",
        short_constant="finderinfo",
        constant=FinderInfo,
        type_=str,
        list=False,
        as_list=False,
        class_=_AttributeFinderInfo,
        append=False,
        update=False,
        help="Info set by the Finder, for example tag color.  Colors can also be set by _kMDItemUserTags.  "
        + f"{FinderInfo} is controlled by the Finder and it's recommended you don't directly access this attribute.  "
        + "If you set or remove a color tag via _kMDItemUserTag, osxmetadata will automatically handle "
        + "processing of FinderInfo color tag.",
        api_help=None,
    ),
    "duedate": Attribute(
        name="duedate",
        short_constant="kMDItemDueDate",
        constant=kMDItemDueDate,
        type_=datetime.datetime,
        list=False,
        as_list=False,
        class_=datetime.datetime,
        append=False,
        update=False,
        help="The date the item is due.  A date in ISO 8601 format, "
        "time and timezone offset are optional: e.g. "
        + "2020-04-14T12:00:00 (ISO 8601 w/o timezone), "
        + "2020-04-14 (ISO 8601 w/o time and time zone), or "
        + "2020-04-14T12:00:00-07:00 (ISO 8601 with timezone offset). "
        + "Times without timezone offset are assumed to be in local timezone.",
        api_help="The date the item is due.  A datetime.datetime object.  "
        + "If datetime.datetime object lacks tzinfo (i.e. it is timezone naive), it "
        + "will be assumed to be in local timezone.",
    ),
    "rating": Attribute(
        name="rating",
        short_constant="kMDItemStarRating",
        constant=kMDItemStarRating,
        type_=int,
        list=False,
        as_list=False,
        class_=int,
        append=False,
        update=False,
        help="User rating of this item. "
        + "For example, the stars rating of an iTunes track. An integer.",
        api_help=None,
    ),
    "participants": Attribute(
        name="participants",
        short_constant="kMDItemParticipants",
        constant=kMDItemParticipants,
        type_=str,
        list=True,
        as_list=False,
        class_=_AttributeList,
        append=True,
        update=True,
        help="The list of people who are visible in an image or movie or written about in a document. "
        + "A list of strings.",
        api_help=None,
    ),
    "projects": Attribute(
        name="projects",
        short_constant="kMDItemProjects",
        constant=kMDItemProjects,
        type_=str,
        list=True,
        as_list=False,
        class_=_AttributeList,
        append=True,
        update=True,
        help="The list of projects that this file is part of. For example, if you were working on a movie all of the files could be marked as belonging to the project “My Movie”. "
        + "A list of strings.",
        api_help=None,
    ),
    "version": Attribute(
        name="version",
        short_constant="kMDItemVersion",
        constant=kMDItemVersion,
        type_=str,
        list=False,
        as_list=False,
        class_=str,
        append=True,
        update=False,
        help="The version number of this file. A string.",
        api_help=None,
    ),
    "stationary": Attribute(
        name="stationary",
        short_constant="kMDItemFSIsStationery",
        constant=kMDItemFSIsStationery,
        type_=bool,
        list=False,
        as_list=False,
        class_=bool,
        append=False,
        update=False,
        help="Boolean indicating if this file is stationery.",
        api_help=None,
    ),
    "findercolor": Attribute(
        name="findercolor",
        short_constant="findercolor",
        constant=FinderInfo,
        type_=str,
        list=False,
        as_list=False,
        class_=_AttributeFinderColor,
        append=False,
        update=False,
        help="Color tag set by the Finder.  Colors can also be set by _kMDItemUserTags.  "
        + "This is controlled by the Finder and it's recommended you don't directly access this attribute.  "
        + "If you set or remove a color tag via _kMDItemUserTag, osxmetadata will automatically handle "
        + "processing of FinderInfo color tag.",
        api_help=None,
    ),
}

# used for formatting output of --list
_SHORT_NAME_WIDTH = max(len(x) for x in ATTRIBUTES) + 5
_LONG_NAME_WIDTH = max(len(x.constant) for x in ATTRIBUTES.values()) + 10
_CONSTANT_WIDTH = 21 + 5  # currently longest is kMDItemDownloadedDate


ATTRIBUTE_DISPATCH = {}
for attr in ATTRIBUTES.values():
    try:
        ATTRIBUTE_DISPATCH[attr.constant].append(attr.name)
    except KeyError:
        ATTRIBUTE_DISPATCH[attr.constant] = [attr.name]

# also add entries for attributes by constant and short constant
# do this after computing widths above
_temp_attributes = {}
for attribute in ATTRIBUTES.values():
    if attribute.constant in ATTRIBUTES:
        raise ValueError(f"Duplicate attribute in ATTRIBUTES: {attribute}")
    _temp_attributes[attribute.constant] = attribute
    _temp_attributes[attribute.short_constant] = attribute
if _temp_attributes:
    ATTRIBUTES.update(_temp_attributes)

def validate_attribute_value(attribute, value):
    """validate that value is compatible with attribute.type_
    and convert value to correct type
    returns value as type attribute.type_
    value may be a single value or a list depending on what attribute expects
    if value contains None, returns None"""

    # check to see if we got None
    try:
        if None in value:
            return None
    except TypeError:
        if value is None:
            return None

    try:
        if isinstance(value, str):
            value = [value]
        else:
            iter(value)
    except TypeError:
        value = [value]

    if not attribute.list and len(value) > 1:
        # got a list but didn't expect one
        raise ValueError(
            f"{attribute.name} expects only one value but list of {len(value)} provided"
        )

    new_values = []
    for val in value:
        new_val = None
        if attribute.type_ == str:
            new_val = str(val)
        elif attribute.type_ == float:
            try:
                new_val = float(val)
            except ValueError:
                # todo: should this really raise ValueError?
                raise TypeError(
                    f"{val} cannot be converted to expected type {attribute.type_}"
                )
        elif attribute.type_ == int:
            try:
                new_val = int(val)
            except ValueError:
                raise TypeError(
                    f"{val} cannot be converted to expected type {attribute.type_}"
                )
        elif attribute.type_ == bool:
            try:
                new_val = bool(val)
            except ValueError:
                raise TypeError(
                    f"{val} cannot be converted to expected type {attribute.type_}"
                )
        elif attribute.type_ == datetime.datetime:
            if isinstance(val, datetime.datetime):
                new_val = val
            elif not val:
                new_val = None
            else:
                try:
                    new_val = datetime.datetime.fromisoformat(val)
                except ValueError:
                    raise TypeError(
                        f"{val} cannot be converted to expected type {attribute.type_}"
                    )
            if isinstance(new_val, datetime.datetime):
                if not datetime_has_tz(new_val):
                    # assume it's in local time, so add local timezone,
                    # convert to UTC, then drop timezone
                    new_val = datetime_naive_to_local(new_val)
                # convert to UTC and remove timezone
                new_val = datetime_tz_to_utc(new_val)
                new_val = datetime_remove_tz(new_val)
        else:
            raise TypeError(f"Unknown type: {type(val)}")
        new_values.append(new_val)

    if attribute.list:
        return new_values
    else:
        return new_values[0]
