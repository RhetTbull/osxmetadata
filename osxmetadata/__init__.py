""" Python module to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """

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
)
from .utils import (
    _debug,
    _get_logger,
    _set_debug,
    set_finder_comment,
    validate_attribute_value,
)

# this was inspired by osx-tags by "Ben S / scooby" and is published under
# the same MIT license. See: https://github.com/scooby/osx-tags

# TODO: What to do about colors
# TODO: Add ability to remove key instead of just clear contents
# TODO: check what happens if OSXMetaData.__init__ called with invalid file--should result in error but saw one case where it didn't
# TODO: cleartags does not always clear colors--this is a new behavior, did Mac OS change something in implementation of colors?

# what to import
__all__ = ["OSXMetaData"]


class _NullsInString(Exception):
    """Nulls in string."""


def _onError(e):
    sys.stderr.write(str(e) + "\n")


class OSXMetaData:
    """Create an OSXMetaData object to access file metadata"""

    __slots__ = [
        "_fname",
        "_posix_name",
        "_attrs",
        "__init",
        "authors",
        "creator",
        "description",
        "downloadeddate",
        "findercomment",
        "headline",
        "keywords",
        "tags",
        "wherefroms",
        "test",
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
        # self.tags = _AttributeTagsSet(ATTRIBUTES["tags"], self._attrs)
        # ATTRIBUTES contains both long and short names, want only the short names (attribute.name)
        for name in set([attribute.name for attribute in ATTRIBUTES.values()]):
            attribute = ATTRIBUTES[name]
            if attribute.class_ not in [str, float]:
                super().__setattr__(name, attribute.class_(attribute, self._attrs))

        # Done with initialization
        self.__init = True

    # @property
    # def finder_comment(self):
    #     """ Get/set the Finder comment (or None) associated with the file.
    #         Functions as a string: e.g. finder_comment += 'my comment'. """
    #     self._load_findercomment()
    #     return self._data[_FINDER_COMMENT]

    # @finder_comment.setter
    # def finder_comment(self, fc):
    #     """ Get/set the Finder comment (or None) associated with the file.
    #         Functions as a string: e.g. finder_comment += 'my comment'. """
    #     # TODO: this creates a temporary script file which gets runs by osascript every time
    #     #       not very efficient.  Perhaps use py-applescript in the future but that increases
    #     #       dependencies + PyObjC

    #     if fc is None:
    #         fc = ""
    #     elif not isinstance(fc, str):
    #         raise TypeError("Finder comment must be strings")

    #     if len(fc) > _MAX_FINDERCOMMENT:
    #         raise ValueError(
    #             "Finder comment limited to %d characters" % _MAX_FINDERCOMMENT
    #         )

    #     fname = self._posix_name
    #     set_finder_comment(fname, fc)
    #     self._load_findercomment()

    # @property
    # def where_from(self):
    #     """ Get/set list of URL(s) where file was downloaded from. """
    #     self._load_download_wherefrom()
    #     return self._data[_WHERE_FROM]

    # @where_from.setter
    # def where_from(self, wf):
    #     """ Get/set list of URL(s) where file was downloaded from. """
    #     if wf is None:
    #         wf = []
    #     elif not isinstance(wf, list):
    #         raise TypeError("Where from must be a list of one or more URL strings")

    #     for w in wf:
    #         if len(w) > _MAX_WHEREFROM:
    #             raise ValueError(
    #                 "Where from URL limited to %d characters" % _MAX_WHEREFROM
    #             )

    #     wf_plist = plistlib.dumps(wf, fmt=FMT_BINARY)
    #     self._attrs.set(_WHERE_FROM, wf_plist)
    #     self._load_download_wherefrom()

    # @property
    # def download_date(self):
    #     """ Get/set date file was downloaded, as a datetime.datetime object. """
    #     self._load_download_date()
    #     return self._data[_DOWNLOAD_DATE]

    # @download_date.setter
    # def download_date(self, dt):
    #     """ Get/set date file was downloaded, as a datetime.datetime object. """
    #     if dt is None:
    #         dt = []
    #     elif not isinstance(dt, datetime.datetime):
    #         raise TypeError("Download date must be a datetime object")

    #     dt_plist = plistlib.dumps([dt], fmt=FMT_BINARY)
    #     self._attrs.set(_DOWNLOAD_DATE, dt_plist)
    #     self._load_download_date()

    @property
    def name(self):
        """ POSIX path of the file OSXMetaData is operating on """
        return self._fname.resolve().as_posix()

    ### Experimenting with generic method of reading / writing attributes
    def get_attribute(self, attribute):
        """ load attribute and return value or None if attribute was not set 
            attribute: an osxmetadata Attribute namedtuple
        """
        logging.debug(f"get: {attribute}")
        if not isinstance(attribute, Attribute):
            raise TypeError(
                "attribute must be osxmetada.constants.Attribute namedtuple"
            )

        try:
            plist = plistlib.loads(self._attrs[attribute.constant])
        except KeyError:
            plist = None

        # TODO: should I check Attribute.type_ is correct?
        if attribute.as_list and isinstance(plist, list):
            return plist[0]
        else:
            return plist

    def get_attribute_str(self, attribute):
        """ returns a string representation of attribute value
            e.g. if attribute is a datedate.datetime object, will 
            format using datetime.isoformat() """
        value = self.get_attribute(attribute)
        try:
            iter(value)
            # must be an interable
            if type(value[0]) == datetime.datetime:
                new_value = [v.isoformat() for v in value]
                return str(new_value)
            return str(value)
        except TypeError:
            # not an iterable
            if type(value) == datetime.datetime:
                return value.isoformat()
            return value

    def set_attribute(self, attribute, value):
        """ write attribute to file
            attribute: an osxmetadata Attribute namedtuple """
        if not isinstance(attribute, Attribute):
            raise TypeError(
                "attribute must be osxmetada.constants.Attribute namedtuple"
            )

        # verify type is correct
        if attribute.list and type(value) == list:
            for val in value:
                if attribute.type_ != type(val):
                    raise ValueError(
                        f"Expected type {attribute.type_} but value is type {type(val)}"
                    )
        elif not attribute.list and type(value) == list:
            raise TypeError(f"Expected single value but got list for {attribute.type_}")
        else:
            if attribute.type_ != type(value):
                raise ValueError(
                    f"Expected type {attribute.type_} but value is type {type(value)}"
                )

        if attribute.as_list:
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

    def update_attribute(self, attribute, value):
        """ Update attribute with union of itself and value
            (this avoids adding duplicate values to attribute)
            attribute: an osxmetadata Attribute namedtuple
            value: value to append to attribute """
        return self.append_attribute(attribute, value, update=True)

    def append_attribute(self, attribute, value, update=False):
        """ append value to attribute
            attribute: an osxmetadata Attribute namedtuple
            value: value to append to attribute
            update: (bool) if True, update instead of append (e.g. avoid adding duplicates)
                    (default is False) """

        logging.debug(f"append_attribute: {attribute} {value}")
        if not isinstance(attribute, Attribute):
            raise TypeError(
                "attribute must be osxmetada.constants.Attribute namedtuple"
            )

        # start with existing values
        new_value = self.get_attribute(attribute)

        # verify type is correct
        if attribute.list and type(value) == list:
            # expected a list, got a list
            for val in value:
                # check type of each element in list
                if attribute.type_ != type(val):
                    raise ValueError(
                        f"Expected type {attribute.type_} but value is type {type(val)}"
                    )
                else:
                    if new_value:
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
        elif not attribute.list and type(value) == list:
            raise TypeError(f"Expected single value but got list for {attribute.type_}")
        else:
            # expected scalar, got a scalar, check type is correct
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

    def remove_attribute(self, attribute, value):
        """ remove a value from attribute, raise exception if attribute does not contain value
            only applies to multi-valued attributes, otherwise raises TypeError """

        if not isinstance(attribute, Attribute):
            raise TypeError(
                "attribute must be osxmetada.constants.Attribute namedtuple"
            )

        if not attribute.list:
            raise TypeError("remove only applies to multi-valued attributes")

        values = self.get_attribute(attribute)
        values.remove(value)
        self.set_attribute(attribute, values)

    def discard_attribute(self, attribute, value):
        """ remove a value from attribute, unlike remove, does not raise exception
            if attribute does not contain value
            only applies to multi-valued attributes, otherwise raises TypeError """

        if not isinstance(attribute, Attribute):
            raise TypeError(
                "attribute must be osxmetada.constants.Attribute namedtuple"
            )

        if not attribute.list:
            raise TypeError("discard only applies to multi-valued attributes")

        values = self.get_attribute(attribute)
        try:
            values.remove(value)
            self.set_attribute(attribute, values)
        except:
            pass

    def clear_attribute(self, attribute):
        """ clear attribute (remove) 
        attribute: an osxmetadata Attribute namedtuple """

        if not isinstance(attribute, Attribute):
            raise TypeError(
                "attribute must be osxmetada.constants.Attribute namedtuple"
            )

        try:
            if attribute.name in _FINDER_COMMENT_NAMES:
                # Finder Comment needs special handling
                # code following will also clear the attribute for Finder Comment
                set_finder_comment(self._posix_name, "")
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
            otherwise raise AttributeError """
        value = self.get_attribute(ATTRIBUTES[name])
        return value

    def __setattr__(self, name, value):
        """ if attribute name is in ATTRIBUTE dict, set the value
            otherwise raise AttributeError """
        try:
            if self.__init:
                # already initialized
                attribute = ATTRIBUTES[name]
                value = validate_attribute_value(attribute, value)
                if value is None:
                    self.clear_attribute(attribute)
                else:
                    self.set_attribute(attribute, value)
        except (KeyError, AttributeError):
            super().__setattr__(name, value)

    # @property
    # def colors(self):
    #     """ return list of color labels from tags
    #         do not return None (e.g. ignore tags with no color)
    #     """
    #     colors = []
    #     if self._tags:
    #         for t in self._tags.keys():
    #             c = self._tags[t]
    #             if c == 0: continue
    #             colors.append(_COLORIDS[c])
    #         return colors
    #     else:
    #         return None

    # def _load_findercomment(self):
    #     try:
    #         # load the binary plist value
    #         self._data[_FINDER_COMMENT] = plistlib.loads(self._attrs[_FINDER_COMMENT])
    #     except KeyError:
    #         self._data[_FINDER_COMMENT] = None

    # def _load_download_wherefrom(self):
    #     try:
    #         # load the binary plist value
    #         self._data[_WHERE_FROM] = plistlib.loads(self._attrs[_WHERE_FROM])
    #     except KeyError:
    #         self._data[_WHERE_FROM] = None

    # def _load_download_date(self):
    #     try:
    #         # load the binary plist value
    #         # returns an array with a single datetime.datetime object
    #         self._data[_DOWNLOAD_DATE] = plistlib.loads(self._attrs[_DOWNLOAD_DATE])[0]
    #         # logger.debug(self._downloaddate)
    #     except KeyError:
    #         self._data[_DOWNLOAD_DATE] = None
