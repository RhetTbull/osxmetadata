""" Python package to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """


# this was inspired by osx-tags by "Ben S / scooby" and is published under
# the same MIT license. See: https://github.com/scooby/osx-tags

import datetime
import json
import logging
import pathlib
import plistlib
import sys

# plistlib creates constants at runtime which causes pylint to complain
from plistlib import FMT_BINARY  # pylint: disable=E0611

import xattr

from ._version import __version__
from .attributes import ATTRIBUTES, Attribute, validate_attribute_value
from .classes import _AttributeList, _AttributeTagsList
from .constants import (
    _COLORIDS,
    _COLORNAMES,
    _FINDER_COMMENT_NAMES,
    _MAX_FINDERCOMMENT,
    _MAX_WHEREFROM,
    _VALID_COLORIDS,
    _kMDItemUserTags,
    kMDItemAuthors,
    kMDItemComment,
    kMDItemCopyright,
    kMDItemCreator,
    kMDItemDescription,
    kMDItemDownloadedDate,
    kMDItemFinderComment,
    kMDItemHeadline,
    kMDItemKeywords,
    kMDItemUserTags,
    kMDItemWhereFroms,
)
from .utils import (
    _debug,
    _get_logger,
    _set_debug,
    clear_finder_comment,
    datetime_naive_to_utc,
    datetime_remove_tz,
    datetime_utc_to_local,
    set_finder_comment,
)

__all__ = [
    "OSXMetaData",
    "__version__",
    "ATTRIBUTES",
    "kMDItemAuthors",
    "kMDItemComment",
    "kMDItemCopyright",
    "kMDItemCreator",
    "kMDItemDescription",
    "kMDItemDownloadedDate",
    "kMDItemFinderComment",
    "kMDItemHeadline",
    "kMDItemKeywords",
    "kMDItemUserTags",
    "_kMDItemUserTags",
    "kMDItemWhereFroms",
]


# TODO: What to do about colors
# TODO: check what happens if OSXMetaData.__init__ called with invalid file--should result in error but saw one case where it didn't
# TODO: cleartags does not always clear colors--this is a new behavior, did Mac OS change something in implementation of colors?


class OSXMetaData:
    """Create an OSXMetaData object to access file metadata"""

    __slots__ = [
        "_fname",
        "_posix_name",
        "_attrs",
        "_tz_aware",
        "__init",
        "authors",
        "comment",
        "copyright",
        "creator",
        "description",
        "downloadeddate",
        "findercomment",
        "headline",
        "keywords",
        "tags",
        "wherefroms",
    ]

    def __init__(self, fname, tz_aware=False):
        """Create an OSXMetaData object to access file metadata
            fname: filename to operate on
            timezone_aware: bool; if True, date/time attributes will return 
                      timezone aware datetime.dateime attributes; if False (default)
                      date/time attributes will return timezone naive objects """
        self._fname = pathlib.Path(fname)
        self._posix_name = self._fname.resolve().as_posix()
        self._tz_aware = tz_aware

        if not self._fname.exists():
            raise FileNotFoundError("file does not exist: ", fname)

        self._attrs = xattr.xattr(self._fname)

        # create property classes for the multi-valued attributes
        # tags get special handling due to color labels
        # ATTRIBUTES contains both long and short names, want only the short names (attribute.name)
        for name in set([attribute.name for attribute in ATTRIBUTES.values()]):
            attribute = ATTRIBUTES[name]
            if attribute.class_ not in [str, float, datetime.datetime]:
                super().__setattr__(
                    name, attribute.class_(attribute, self._attrs, self)
                )

        # Done with initialization
        self.__init = True

    @property
    def name(self):
        """ POSIX path of the file OSXMetaData is operating on """
        return self._fname.resolve().as_posix()

    @property
    def tz_aware(self):
        """ returns the timezone aware flag """
        return self._tz_aware

    @tz_aware.setter
    def tz_aware(self, tz_flag):
        """ sets the timezone aware flag
            tz_flag: bool """
        self._tz_aware = tz_flag

    def _to_dict(self):
        """ Return dict with all attributes for this file 
            key of dict is filename and value is another dict with attributes """

        attribute_list = self.list_metadata()
        json_data = {}
        json_data["_version"] = __version__
        json_data["_filepath"] = self._posix_name
        json_data["_filename"] = self._fname.name
        for attr in attribute_list:
            try:
                attribute = ATTRIBUTES[attr]
                if attribute.type_ == datetime.datetime:
                    # need to convert datetime.datetime to string to serialize
                    value = self.get_attribute(attribute.name)
                    if type(value) == list:
                        value = [v.isoformat() for v in value]
                    else:
                        value = value.isoformat()
                    json_data[attribute.constant] = value
                else:
                    # get raw value
                    json_data[attribute.constant] = self.get_attribute(attribute.name)
            except KeyError:
                # unknown attribute, ignore it
                pass
        return json_data

    def to_json(self):
        """ Returns a string in JSON format for all attributes in this file """
        json_data = self._to_dict()
        json_str = json.dumps(json_data)
        return json_str

    def _restore_attributes(self, attr_dict):
        """ restore attributes from attr_dict
            for each attribute in attr_dict, will set the attribute
            will not clear/erase any attributes on file that are not in attr_dict
            attr_dict: an attribute dict as produced by OSXMetaData._to_dict() """

        for key, val in attr_dict.items():
            if key.startswith("_"):
                # skip private keys like _version and _filepath
                continue
            try:
                self.set_attribute(key, val)
            except:
                logging.warning(f"Unable to restore attribute {attr} for {self._fname}")

    def get_attribute(self, attribute_name):
        """ load attribute and return value or None if attribute was not set 
            attribute_name: name of attribute
        """

        attribute = ATTRIBUTES[attribute_name]
        logging.debug(f"get: {attribute}")

        # user tags need special processing to normalize names
        if attribute.name == "tags":
            self.tags._load_data()
            return self.tags.data

        try:
            plist = plistlib.loads(self._attrs[attribute.constant])
        except KeyError:
            plist = None

        # add UTC to any datetime.datetime objects because that's how MacOS stores them
        # In the plist associated with extended metadata attributes, times are stored as:
        # <date>2020-04-14T14:49:22Z</date>
        if plist and isinstance(plist, list):
            if isinstance(plist[0], datetime.datetime):
                plist = [datetime_naive_to_utc(d) for d in plist]
                if not self._tz_aware:
                    # want datetimes in naive format
                    plist = [
                        datetime_remove_tz(d_local)
                        for d_local in [datetime_utc_to_local(d_utc) for d_utc in plist]
                    ]
        elif isinstance(plist, datetime.datetime):
            plist = datetime_naive_to_utc(plist)
            if not self._tz_aware:
                # want datetimes in naive format
                plist = datetime_remove_tz(datetime_utc_to_local(plist))

        if attribute.as_list and isinstance(plist, list):
            return plist[0]
        else:
            return plist

    def get_attribute_str(self, attribute_name):
        """ returns a string representation of attribute value
            e.g. if attribute is a datedate.datetime object, will 
            format using datetime.isoformat()
            attribute_name: name of attribute """
        value = self.get_attribute(attribute_name)
        if type(value) == list or type(value) == set:
            if type(value[0]) == datetime.datetime:
                new_value = [v.isoformat() for v in value]
                return str(new_value)
            return str(value)
        else:
            if type(value) == datetime.datetime:
                return value.isoformat()
            return value

    def set_attribute(self, attribute_name, value):
        """ write attribute to file with value
            attribute_name: an osxmetadata Attribute name
            value: value to store in attribute """
        attribute = ATTRIBUTES[attribute_name]

        # user tags need special processing to normalize names
        if attribute.name == "tags":
            return self.tags.set_value(value)

        # verify type is correct
        value = validate_attribute_value(attribute, value)

        if attribute.name in _FINDER_COMMENT_NAMES:
            # Finder Comment needs special handling
            # code following will also set the attribute for Finder Comment
            set_finder_comment(self._posix_name, value)
        elif attribute.class_ in [_AttributeList, _AttributeTagsList]:
            getattr(self, attribute.name).set_value(value)
        else:
            # must be a normal scalar (e.g. str, float)
            plist = plistlib.dumps(value, fmt=FMT_BINARY)
            self._attrs.set(attribute.constant, plist)

        return value

    def update_attribute(self, attribute_name, value):
        """ Update attribute with union of itself and value
            (this avoids adding duplicate values to attribute)
            attribute: an osxmetadata Attribute name
            value: value to append to attribute """
        return self.append_attribute(attribute_name, value, update=True)

    def append_attribute(self, attribute_name, value, update=False):
        """ append value to attribute
            attribute_name: an osxmetadata Attribute name
            value: value to append to attribute
            update: (bool) if True, update instead of append (e.g. avoid adding duplicates)
                    (default is False) """

        attribute = ATTRIBUTES[attribute_name]
        logging.debug(f"append_attribute: {attribute} {value}")

        # start with existing values
        new_value = self.get_attribute(attribute.name)

        value = validate_attribute_value(attribute, value)

        if attribute.list:
            if new_value is not None:
                new_value = list(new_value)
                if update:
                    for val in value:
                        if val not in new_value:
                            new_value.append(val)
                else:
                    new_value.extend(value)
            else:
                # no original value
                new_value = value
        else:
            # scalar value
            if update:
                raise AttributeError(f"Cannot use update on {attribute.type_}")
            if new_value is not None:
                new_value += value
            else:
                new_value = value

        try:
            if attribute.name in _FINDER_COMMENT_NAMES:
                # Finder Comment needs special handling
                # code following will also set the attribute for Finder Comment
                set_finder_comment(self._posix_name, new_value)
                plist = plistlib.dumps(new_value, fmt=FMT_BINARY)
                self._attrs.set(attribute.constant, plist)
            elif attribute.class_ in [_AttributeList, _AttributeTagsList]:
                # if tags, set_value will normalize
                getattr(self, attribute.name).set_value(new_value)
            else:
                plist = plistlib.dumps(new_value, fmt=FMT_BINARY)
                self._attrs.set(attribute.constant, plist)
        except Exception as e:
            # todo: should catch this or not?
            raise e

        return new_value

    def remove_attribute(self, attribute_name, value):
        """ remove a value from attribute, raise ValueError if attribute does not contain value
            only applies to multi-valued attributes, otherwise raises TypeError
            attribute_name: name of OSXMetaData attribute """

        attribute = ATTRIBUTES[attribute_name]

        if not attribute.list:
            raise TypeError("remove only applies to multi-valued attributes")

        if attribute.name == "tags":
            # tags need special processing
            self.tags.remove(value)
        else:
            values = self.get_attribute(attribute.name)
            values = list(values)
            values.remove(value)
            self.set_attribute(attribute.name, values)

    def discard_attribute(self, attribute_name, value):
        """ remove a value from attribute, unlike remove, does not raise exception
            if attribute does not contain value
            only applies to multi-valued attributes, otherwise raises TypeError
            attribute_name: name of OSXMetaData attribute """

        attribute = ATTRIBUTES[attribute_name]

        if not attribute.list:
            raise TypeError("discard only applies to multi-valued attributes")

        values = self.get_attribute(attribute.name)
        try:
            values.remove(value)
            self.set_attribute(attribute.name, values)
        except:
            pass

    def clear_attribute(self, attribute_name):
        """ clear anttribute (remove it from the file) 
            attribute_name: name of OSXMetaData attribute """

        attribute = ATTRIBUTES[attribute_name]

        try:
            if attribute.name in _FINDER_COMMENT_NAMES:
                # Finder Comment needs special handling
                # code following will also clear the attribute for Finder Comment
                clear_finder_comment(self._posix_name)
            self._attrs.remove(attribute.constant)
        except (IOError, OSError):
            # TODO: fix this try/except handling
            pass

    def _list_attributes(self):
        """ list the attributes set on the file """
        return self._attrs.list()

    def list_metadata(self):
        """ list the Apple metadata attributes set on the file:
            e.g. those in com.apple.metadata namespace """
        # also lists com.osxmetadata.test used for debugging
        mdlist = self._attrs.list()
        mdlist = [
            md
            for md in mdlist
            if md.startswith("com.apple.metadata")
            or md.startswith("com.osxmetadata.test")
        ]
        return mdlist

    def __getattr__(self, name):
        """ if attribute name is in ATTRIBUTE dict, return the value
            otherwise raise KeyError """
        value = self.get_attribute(name)
        return value

    def __setattr__(self, name, value):
        """ if object is initialized and name is an attribute in ATTRIBUTES, 
            set the attribute to value
            if value value is None, will clear (delete) the attribute and all associated values
            if name is not a metadata attribute, assume it's a normal class attribute and pass to
            super() to handle  """
        try:
            if self.__init:
                # already initialized
                attribute = ATTRIBUTES[name]
                if value is None:
                    self.clear_attribute(attribute.name)
                else:
                    self.set_attribute(attribute.name, value)
        except (KeyError, AttributeError):
            super().__setattr__(name, value)
