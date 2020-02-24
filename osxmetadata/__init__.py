""" Python module to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """


# this was inspired by osx-tags by "Ben S / scooby" and is published under
# the same MIT license. See: https://github.com/scooby/osx-tags

import datetime
import logging
import pathlib
import plistlib
import sys

# plistlib creates constants at runtime which causes pylint to complain
from plistlib import FMT_BINARY  # pylint: disable=E0611

import xattr

from .attributes import ATTRIBUTES, Attribute
from .classes import _AttributeList, _AttributeTagsSet
from .constants import (  # _DOWNLOAD_DATE,; _FINDER_COMMENT,; _TAGS,; _WHERE_FROM,
    _COLORIDS,
    _COLORNAMES,
    _FINDER_COMMENT_NAMES,
    _MAX_FINDERCOMMENT,
    _MAX_WHEREFROM,
    _VALID_COLORIDS,
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
    _kMDItemUserTags,
    kMDItemWhereFroms,
)
from .utils import (
    _debug,
    _get_logger,
    _set_debug,
    set_finder_comment,
    clear_finder_comment,
    validate_attribute_value,
)

__all__ = [
    "OSXMetaData",
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

    def __init__(self, fname):
        """Create an OSXMetaData object to access file metadata"""
        self._fname = pathlib.Path(fname)
        self._posix_name = self._fname.resolve().as_posix()

        if not self._fname.exists():
            raise FileNotFoundError("file does not exist: ", fname)

        self._attrs = xattr.xattr(self._fname)

        # create property classes for the multi-valued attributes
        # tags get special handling due to color labels
        # ATTRIBUTES contains both long and short names, want only the short names (attribute.name)
        for name in set([attribute.name for attribute in ATTRIBUTES.values()]):
            attribute = ATTRIBUTES[name]
            if attribute.class_ not in [str, float, datetime.datetime]:
                super().__setattr__(name, attribute.class_(attribute, self._attrs))

        # Done with initialization
        self.__init = True

    @property
    def name(self):
        """ POSIX path of the file OSXMetaData is operating on """
        return self._fname.resolve().as_posix()

    def get_attribute(self, attribute_name):
        """ load attribute and return value or None if attribute was not set 
            attribute_name: name of attribute
        """

        attribute = ATTRIBUTES[attribute_name]
        logging.debug(f"get: {attribute}")

        # user tags need special processing to normalize names
        if attribute.name == "tags":
            return self.tags

        try:
            plist = plistlib.loads(self._attrs[attribute.constant])
        except KeyError:
            plist = None

        # TODO: should I check Attribute.type_ is correct?
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
        # verify type is correct
        if attribute.list and (type(value) == list or type(value) == set):
            for val in value:
                if attribute.type_ != type(val):
                    raise ValueError(
                        f"Expected type {attribute.type_} but value is type {type(val)}"
                    )
        elif not attribute.list and (type(value) == list or type(value) == set):
            raise TypeError(f"Expected single value but got list for {attribute.type_}")
        elif attribute.type_ != type(value):
            raise ValueError(
                f"Expected type {attribute.type_} but value is type {type(value)}"
            )

        if attribute.as_list and (type(value) != list and type(value) != set):
            # some attributes like kMDItemDownloadedDate are stored in a list
            # even though they only have only a single value
            value = [value]

        if attribute.name in _FINDER_COMMENT_NAMES:
            # Finder Comment needs special handling
            # code following will also set the attribute for Finder Comment
            set_finder_comment(self._posix_name, value)
        elif attribute.class_ in [_AttributeList, _AttributeTagsSet]:
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

        # verify type is correct
        if attribute.list and (type(value) == list or type(value) == set):
            # expected a list, got a list
            for val in value:
                # check type of each element in list
                if attribute.type_ != type(val):
                    raise ValueError(
                        f"Expected type {attribute.type_} but value is type {type(val)}"
                    )
                else:
                    if new_value:
                        new_value = list(new_value)
                        if update:
                            # if update, only add values not already in the list
                            # behaves like set.update
                            for v in value:
                                if v not in new_value:
                                    new_value.append(v)
                        else:
                            # not update, add all values
                            new_value.extend(value)
                    else:
                        if update:
                            # no previous values but still need to make sure we don't have
                            # dupblicate values: convert to set & back to list
                            new_value = list(set(value))
                        else:
                            # no previous values, set new_value to whatever value is
                            new_value = value
        elif not attribute.list and (type(value) == list or type(value) == set):
            raise TypeError(f"Expected single value but got list for {attribute.type_}")
        else:
            # got a scalar, check type is correct
            if attribute.type_ != type(value):
                raise ValueError(
                    f"Expected type {attribute.type_} but value is type {type(value)}"
                )
            else:
                # not a list, could be str, float, datetime.datetime
                if update:
                    raise AttributeError(f"Cannot use update on {attribute.type_}")
                if new_value:
                    new_value += value
                else:
                    new_value = value

        if attribute.as_list:
            # some attributes like kMDItemDownloadedDate are stored in a list
            # even though they only have only a single value
            new_value = [new_value]

        try:
            if attribute.name in _FINDER_COMMENT_NAMES:
                # Finder Comment needs special handling
                # code following will also set the attribute for Finder Comment
                set_finder_comment(self._posix_name, new_value)

            plist = plistlib.dumps(new_value, fmt=FMT_BINARY)
            self._attrs.set(attribute.constant, plist)
        except Exception as e:
            # todo: should catch this or not?
            raise e

        return new_value

    def remove_attribute(self, attribute_name, value):
        """ remove a value from attribute, raise exception if attribute does not contain value
            only applies to multi-valued attributes, otherwise raises TypeError
            attribute_name: name of OSXMetaData attribute """

        attribute = ATTRIBUTES[attribute_name]

        if not attribute.list:
            raise TypeError("remove only applies to multi-valued attributes")

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
        """ clear anttribute (remove) 
            attribute_name: name of OSXMetaData attribute """

        attribute = ATTRIBUTES[attribute_name]

        try:
            if attribute.name in _FINDER_COMMENT_NAMES:
                # Finder Comment needs special handling
                # code following will also clear the attribute for Finder Comment
                clear_finder_comment(self._posix_name)
            self._attrs.remove(attribute.constant)
        except (IOError, OSError):
            pass

    def _list_attributes(self):
        """ list the attributes set on the file """
        return self._attrs.list()

    def list_metadata(self):
        """ list the Apple metadata attributes:
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
                value = validate_attribute_value(attribute, value)
                if value is None:
                    self.clear_attribute(attribute.name)
                else:
                    self.set_attribute(attribute.name, value)
        except (KeyError, AttributeError):
            super().__setattr__(name, value)
