""" Constants and validation for metadata attributes that can be set """

import datetime
import logging
from collections import namedtuple

from .classes import _AttributeList, _AttributeTagsList
from .constants import *
from .utils import (
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
# class: the attribute class to use, e.g. _AttributeList or str
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
        "help",
        "api_help",
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
        None,
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
        None,
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
        None,
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
        None,
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
        None,
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
        "The date the item was downloaded.  A date in ISO 8601 format, "
        "time and timezone offset are optional: e.g. "
        + "2020-04-14T12:00:00 (ISO 8601 w/o timezone), "
        + "2020-04-14 (ISO 8601 w/o time and time zone), or "
        + "2020-04-14T12:00:00-07:00 (ISO 8601 with timezone offset). "
        + "Times without timezone offset are assumed to be in local timezone.",
        "The date the item was downloaded.  A datetime.datetime object.  "
        + "If datetime.datetime object lacks tzinfo (i.e. it is timezone naive), it "
        + "will be assumed to be in local timezone.",
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
        None,
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
        None,
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
        None,
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
        None,
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
        None,
    ),
    # "test": Attribute(
    #     "test",
    #     "com.osxmetadata.test:DontTryThisAtHomeKids",
    #     "com.osxmetadata.test:DontTryThisAtHomeKids",
    #     datetime.datetime,
    #     False,
    #     False,
    #     datetime.datetime,
    #     "Don't try this at home",
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


def validate_attribute_value(attribute, value):
    """ validate that value is compatible with attribute.type_ 
        and convert value to correct type
        returns value as type attribute.type_ 
        value may be a single value or a list depending on what attribute expects 
        if value contains None, returns None """

    logging.debug(
        f"validate_attribute_value: attribute: {attribute}, value: {value}, type: {type(value)}"
    )

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

    # # check for None and convert to list if needed
    # if not isinstance(value, list):
    #     if value is None:
    #         return None
    #     value = [value]
    # elif None in value:
    #     return None

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
            except:
                raise TypeError(
                    f"{val} cannot be converted to expected type {attribute.type_}"
                )
        elif attribute.type_ == datetime.datetime:
            if not isinstance(val, datetime.datetime):
                # if not already a datetime.datetime, try to convert it
                try:
                    new_val = datetime.datetime.fromisoformat(val)
                except:
                    raise TypeError(
                        f"{val} cannot be converted to expected type {attribute.type_}"
                    )
            else:
                new_val = val
            # convert datetime to UTC
            if datetime_has_tz(new_val):
                # convert to UTC and remove timezone
                new_val = datetime_tz_to_utc(new_val)
                new_val = datetime_remove_tz(new_val)
            else:
                # assume it's in local time, so add local timezone,
                # convert to UTC, then drop timezone
                new_val = datetime_naive_to_local(new_val)
                new_val = datetime_tz_to_utc(new_val)
                new_val = datetime_remove_tz(new_val)
        else:
            raise TypeError(f"Unknown type: {type(val)}")
        new_values.append(new_val)

    logging.debug(f"new_values = {new_values}")

    if attribute.list:
        return new_values
    else:
        return new_values[0]
