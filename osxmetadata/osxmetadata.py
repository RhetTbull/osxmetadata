""" OSXMetaData class to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """


import base64
import datetime
import json
import logging
import os.path
import pathlib
import plistlib

# plistlib creates constants at runtime which causes pylint to complain
from plistlib import FMT_BINARY  # pylint: disable=E0611

import applescript
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
    FINDER_COLOR_BLUE,
    FINDER_COLOR_GRAY,
    FINDER_COLOR_GREEN,
    FINDER_COLOR_NONE,
    FINDER_COLOR_ORANGE,
    FINDER_COLOR_PURPLE,
    FINDER_COLOR_RED,
    FINDER_COLOR_YELLOW,
    FinderInfo,
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
    kMDItemParticipants,
    kMDItemProjects,
    kMDItemStarRating,
    kMDItemUserTags,
    kMDItemVersion,
    kMDItemWhereFroms,
    kMDItemFSIsStationery,
)
from .datetime_utils import (
    datetime_naive_to_utc,
    datetime_remove_tz,
    datetime_utc_to_local,
)
from .debug import _debug, _get_logger, _set_debug
from .findertags import Tag, get_tag_color_name


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
    "kMDItemDueDate",
    "kMDItemStarRating",
    "kMDItemParticipants",
    "kMDItemProjects",
    "kMDItemVersion",
    "kMDItemFSIsStationery",
]


# TODO: What to do about colors
# TODO: check what happens if OSXMetaData.__init__ called with invalid file--should result in error but saw one case where it didn't
# TODO: cleartags does not always clear colors--this is a new behavior, did Mac OS change something in implementation of colors?

# AppleScript for manipulating Finder comments
_scpt_set_finder_comment = applescript.AppleScript(
    """
            on run {path, fc}
	            set thePath to path
	            set theComment to fc
	            tell application "Finder" to set comment of (POSIX file thePath as alias) to theComment
            end run
            """
)

_scpt_clear_finder_comment = applescript.AppleScript(
    """
            on run {path}
	            set thePath to path
	            set theComment to missing value
	            tell application "Finder" to set comment of (POSIX file thePath as alias) to theComment
            end run
            """
)


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
        "finderinfo",
        "duedate",
        "rating",
        "participants",
        "projects",
        "version",
        "stationary",
        "findercolor",
    ]

    def __init__(self, fname, tz_aware=False):
        """Create an OSXMetaData object to access file metadata
        fname: filename to operate on
        timezone_aware: bool; if True, date/time attributes will return
                  timezone aware datetime.dateime attributes; if False (default)
                  date/time attributes will return timezone naive objects"""
        self._fname = pathlib.Path(fname)
        self._posix_name = self._fname.resolve().as_posix()
        self._tz_aware = tz_aware

        if not self._fname.exists():
            raise FileNotFoundError("file does not exist: ", fname)

        self._attrs = xattr.xattr(self._fname)

        # create property classes for the multi-valued attributes
        # tags get special handling due to color labels
        # ATTRIBUTES contains both long and short names, want only the short names (attribute.name)
        for name in {attribute.name for attribute in ATTRIBUTES.values()}:
            attribute = ATTRIBUTES[name]
            if attribute.class_ not in [str, float, int, bool, datetime.datetime]:
                super().__setattr__(
                    name, attribute.class_(attribute, self._attrs, self)
                )

        # Done with initialization
        self.__init = True

    @property
    def name(self):
        """POSIX path of the file OSXMetaData is operating on"""
        return self._fname.resolve().as_posix()

    @property
    def tz_aware(self):
        """returns the timezone aware flag"""
        return self._tz_aware

    @tz_aware.setter
    def tz_aware(self, tz_flag):
        """sets the timezone aware flag
        tz_flag: bool"""
        self._tz_aware = tz_flag

    def asdict(self, all_=False, encode=True):
        """Return dict with all attributes for this file

        Args:
            all_: bool, if True, returns all attributes including those that osxmetadata knows nothing about
            encode: bool, if True, encodes values for unknown attributes with base64, otherwise leaves the values as raw bytes

        Returns:
            dict with attributes for this file
        """

        attribute_list = self._list_attributes() if all_ else self.list_metadata()
        dict_data = {
            "_version": __version__,
            "_filepath": self._posix_name,
            "_filename": self._fname.name,
        }

        for attr in attribute_list:
            try:
                attribute = ATTRIBUTES[attr]
                if attribute.name == "tags":
                    tags = self.get_attribute(attribute.name)
                    value = [[tag.name, tag.color] for tag in tags]
                    dict_data[attribute.constant] = value
                elif attribute.name == "finderinfo":
                    value = self.finderinfo.asdict()
                    dict_data[attribute.constant] = value
                elif attribute.type_ == datetime.datetime:
                    # need to convert datetime.datetime to string to serialize
                    value = self.get_attribute(attribute.name)
                    if type(value) == list:
                        value = [v.isoformat() for v in value]
                    else:
                        value = value.isoformat()
                    dict_data[attribute.constant] = value
                else:
                    # get raw value
                    dict_data[attribute.constant] = self.get_attribute(attribute.name)
            except KeyError:
                # an attribute osxmetadata doesn't know about
                if all_:
                    try:
                        value = self._attrs[attr]
                        # convert value to base64 encoded ascii
                        if encode:
                            value = base64.b64encode(value).decode("ascii")
                        dict_data[attr] = value
                    except KeyError as e:
                        # value disappeared between call to _list_attributes and now
                        pass
        return dict_data

    def to_json(self, all_=False):
        """Returns a string in JSON format for all attributes in this file

        Args:
            all_: bool; if True, also restores attributes not known to osxmetadata (generated with asdict(all_=True, encode=True) )
        """
        dict_data = self.asdict(all_=all_)
        return json.dumps(dict_data)

    def _restore_attributes(self, attr_dict, all_=False):
        """restore attributes from attr_dict
        for each attribute in attr_dict, will set the attribute
        will not clear/erase any attributes on file that are not in attr_dict

        Args:
            attr_dict: an attribute dict as produced by OSXMetaData.asdict()
            all_: bool; if True, also restores attributes not known to osxmetadata (generated with asdict(all_=True, encode=True) )
        """

        for key, val in attr_dict.items():
            if key.startswith("_"):
                # skip private keys like _version and _filepath
                continue
            try:
                if key == _kMDItemUserTags:
                    if not isinstance(val, list):
                        raise TypeError(
                            f"expected list for attribute {key} but got {type(val)}"
                        )
                    self.set_attribute(key, [Tag(*tag_val) for tag_val in val])
                elif key == FinderInfo:
                    if not isinstance(val, dict):
                        raise TypeError(
                            f"expected dict for attribute {key} but got {type(val)}"
                        )
                    self.set_attribute(key, val)
                elif key in ATTRIBUTES:
                    self.set_attribute(key, val)
                elif all_:
                    self._attrs.set(key, base64.b64decode(val))
            except Exception as e:
                logging.warning(
                    f"Unable to restore attribute {key} for {self._fname}: {e}"
                )

    def get_attribute(self, attribute_name):
        """load attribute and return value or None if attribute was not set
        attribute_name: name of attribute
        """

        attribute = ATTRIBUTES[attribute_name]

        # user tags and finderinfo need special processing
        if attribute.name in ["tags", "finderinfo", "findercolor"]:
            return getattr(self, attribute.name).get_value()

        # must be a "normal" metadata attribute
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
        """returns a string representation of attribute value
        e.g. if attribute is a datedate.datetime object, will
        format using datetime.isoformat()
        attribute_name: name of attribute"""
        value = self.get_attribute(attribute_name)
        if type(value) in [list, set]:
            if value:
                if type(value[0]) == datetime.datetime:
                    new_value = [v.isoformat() for v in value]
                    return str(new_value)
                elif isinstance(value[0], Tag):
                    new_value = [
                        f"{tag.name},{get_tag_color_name(tag.color)}"
                        if tag.color
                        else f"{tag.name}"
                        for tag in value
                    ]
                    return str(new_value)
            return [str(val) for val in value]
        else:
            if type(value) == datetime.datetime:
                return value.isoformat()
            elif isinstance(value, Tag):
                return (
                    f"{value.name},{get_tag_color_name(value.color)}"
                    if value.color
                    else f"{value.name}"
                )
            return str(value)

    def set_attribute(self, attribute_name, value):
        """write attribute to file with value
        attribute_name: an osxmetadata Attribute name
        value: value to store in attribute"""
        attribute = ATTRIBUTES[attribute_name]

        # user tags and Finder info need special processing
        if attribute.name in ["tags", "finderinfo", "findercolor"]:
            return getattr(self, attribute.name).set_value(value)

        # verify type is correct
        value = validate_attribute_value(attribute, value)

        if attribute.name in _FINDER_COMMENT_NAMES:
            # Finder Comment needs special handling
            # code following will also set the attribute for Finder Comment
            self.set_finder_comment(self._posix_name, value)
        elif attribute.class_ in [_AttributeList, _AttributeTagsList]:
            getattr(self, attribute.name).set_value(value)
        else:
            # must be a normal scalar (e.g. str, float)
            plist = plistlib.dumps(value, fmt=FMT_BINARY)
            self._attrs.set(attribute.constant, plist)

    def update_attribute(self, attribute_name, value):
        """Update attribute with union of itself and value
        (this avoids adding duplicate values to attribute)
        attribute: an osxmetadata Attribute name
        value: value to append to attribute"""
        return self.append_attribute(attribute_name, value, update=True)

    def append_attribute(self, attribute_name, value, update=False):
        """append value to attribute
        attribute_name: an osxmetadata Attribute name
        value: value to append to attribute
        update: (bool) if True, update instead of append (e.g. avoid adding duplicates)
                (default is False)"""

        attribute = ATTRIBUTES[attribute_name]

        # start with existing values
        new_value = self.get_attribute(attribute.name)

        # user tags need special processing to normalize names
        if attribute.name == "tags":
            if not isinstance(new_value, list) or not isinstance(value, list):
                raise TypeError(
                    f"tags expects values in list: {type(new_value)}, {type(value)}"
                )

            if update:
                # verify not already in values
                for val in value:
                    if val not in new_value:
                        new_value.append(val)
            else:
                new_value.extend(value)
            return self.tags.set_value(new_value)
        if attribute.name in ["finderinfo", "findercolor"]:
            raise ValueError(f"cannot append or update {attribute.name}")

        value = validate_attribute_value(attribute, value)

        if attribute.list:
            if new_value is None:
                # no original value
                new_value = value
            else:
                new_value = list(new_value)
                if update:
                    for val in value:
                        if val not in new_value:
                            new_value.append(val)
                else:
                    new_value.extend(value)
        else:
            # scalar value
            if update:
                raise AttributeError(f"Cannot use update on {attribute.type_}")
            if new_value is None:
                new_value = value

            else:
                new_value += value
        try:
            if attribute.name in _FINDER_COMMENT_NAMES:
                # Finder Comment needs special handling
                self.set_finder_comment(self._posix_name, new_value)
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
        """remove a value from attribute, raise ValueError if attribute does not contain value
        only applies to multi-valued attributes, otherwise raises TypeError
        attribute_name: name of OSXMetaData attribute"""

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
        """remove a value from attribute, unlike remove, does not raise exception
        if attribute does not contain value
        only applies to multi-valued attributes, otherwise raises TypeError
        attribute_name: name of OSXMetaData attribute"""

        attribute = ATTRIBUTES[attribute_name]

        if not attribute.list:
            raise TypeError("discard only applies to multi-valued attributes")

        values = self.get_attribute(attribute.name)
        try:
            values.remove(value)
            self.set_attribute(attribute.name, values)
        except Exception:
            pass

    def clear_attribute(self, attribute_name):
        """clear anttribute (remove it from the file)
        attribute_name: name of OSXMetaData attribute"""

        attribute = ATTRIBUTES[attribute_name]

        try:
            if attribute.name in _FINDER_COMMENT_NAMES:
                # Finder Comment needs special handling
                # code following will also clear the attribute for Finder Comment
                self.clear_finder_comment(self._posix_name)

            if attribute.name in ["finderinfo", "findercolor", "tags"]:
                # don't clear the entire FinderInfo attribute, just delete the color
                self.finderinfo.set_finderinfo_color(FINDER_COLOR_NONE)

            if attribute.name not in ["finderinfo", "findercolor"]:
                # remove the entire attribute
                self._attrs.remove(attribute.constant)
        except (IOError, OSError):
            # TODO: fix this try/except handling
            pass

    def _list_attributes(self):
        """list all the attributes set on the file"""
        return self._attrs.list()

    def list_metadata(self):
        """list the Apple metadata attributes set on the file:
        e.g. those in com.apple.metadata namespace"""
        # also lists com.osxmetadata.test used for debugging
        mdlist = self._list_attributes()
        mdlist = [
            md
            for md in mdlist
            if md.startswith("com.apple.metadata")
            or md.startswith("com.apple.FinderInfo")
            or md.startswith("com.osxmetadata.test")
        ]
        return mdlist

    def set_finder_comment(self, path, comment):
        """set finder comment for object path (file or directory)
        path: path to file or directory in posix format
        comment: comment string
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Could not find {path}")

        if comment:
            _scpt_set_finder_comment.run(path, comment)
            plist = plistlib.dumps(comment, fmt=FMT_BINARY)
            self._attrs.set(ATTRIBUTES["findercomment"].constant, plist)
        else:
            self.clear_finder_comment(path)

    def clear_finder_comment(self, path):
        """clear finder comment for object path (file or directory)
        path: path to file or directory in posix format
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Could not find {path}")

        _scpt_clear_finder_comment.run(path)
        try:
            self._attrs.remove(ATTRIBUTES["findercomment"].constant)
        except (IOError, OSError):
            # exception raised if attribute not found and attempt to remove it
            pass

    def __getattr__(self, name):
        """if attribute name is in ATTRIBUTE dict, return the value"""
        if name in ATTRIBUTES:
            return self.get_attribute(name)
        raise AttributeError(f"{name} is not an attribute")

    def __setattr__(self, name, value):
        """if object is initialized and name is an attribute in ATTRIBUTES,
        set the attribute to value
        if value value is None, will clear (delete) the attribute and all associated values
        if name is not a metadata attribute, assume it's a normal class attribute and pass to
        super() to handle"""
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
