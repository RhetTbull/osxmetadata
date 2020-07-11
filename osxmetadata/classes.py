""" Classes for metadata attribute types """

import collections.abc
import datetime
import logging
import os
import plistlib
import sys
from plistlib import FMT_BINARY  # pylint: disable=E0611

from .constants import (
    _COLORIDS,
    _COLORNAMES,
    _MAX_FINDER_COLOR,
    _MIN_FINDER_COLOR,
    _VALID_COLORIDS,
    FINDER_COLOR_NONE,
)
from .datetime_utils import (
    datetime_naive_to_utc,
    datetime_remove_tz,
    datetime_utc_to_local,
)
from .debug import _debug
from .findertags import Tag, get_finder_tags, get_finderinfo_color, set_finderinfo_color


class _AttributeList(collections.abc.MutableSequence):
    """ represents a multi-valued OSXMetaData attribute list """

    def __init__(self, attribute, xattr_, osxmetadata_obj):
        """ initialize object
            attribute: an OSXMetaData Attributes namedtuple 
            xattr_: an instance of xattr.xattr
            osxmetadata_obj: instance of OSXMetaData that created this class instance """
        self._attribute = attribute
        self._attrs = xattr_
        self._md = osxmetadata_obj

        self._constant = attribute.constant

        self.data = []
        self._values = []
        self._load_data()

    def set_value(self, value):
        self.data = value
        self._write_data()

    def _load_data(self):
        self._values = []
        try:
            # load the binary plist value
            self._values = plistlib.loads(self._attrs[self._constant])
            if self._values:
                try:
                    self.data = list(self._values)
                    if self._attribute.type_ == datetime.datetime:
                        # add UTC timezone to datetime values
                        # because that's how MacOS stores them
                        # In the plist associated with xattr, times are stored as:
                        # <date>2020-04-14T14:49:22Z</date>
                        self.data = [datetime_naive_to_utc(dt) for dt in self.data]
                        if not self._md._tz_aware:
                            # want datetimes in naive format
                            self.data = [
                                datetime_remove_tz(d_local)
                                for d_local in [
                                    datetime_utc_to_local(d_utc) for d_utc in self.data
                                ]
                            ]
                except TypeError:
                    self.data = set([self._values])
                    if self._attribute.type_ == datetime.datetime:
                        # add UTC timezone to datetime values
                        self.data = {datetime_naive_to_utc(dt) for dt in self.data}
                        if not self._tz_aware:
                            # want datetimes in naive format
                            self.data = {
                                datetime_remove_tz(d_local)
                                for d_local in {
                                    datetime_utc_to_local(d_utc) for d_utc in self.data
                                }
                            }
            else:
                self.data = []
        except KeyError:
            self.data = []

    def sort(self, key=None, reverse=False):
        self._load_data()
        self.data.sort(key=key, reverse=reverse)
        self._write_data()

    def __delitem__(self, index):
        self._load_data()
        self.data.__delitem__(index)
        self._write_data()

    def __getitem__(self, index):
        self._load_data()
        return self.data.__getitem__(index)

    def __len__(self):
        self._load_data()
        return self.data.__len__()

    def __setitem__(self, index, value):
        self._load_data()
        self.data.__setitem__(index, value)
        self._write_data()
        self._load_data()

    def insert(self, index, value):
        self._load_data()
        self.data.insert(index, value)
        self._write_data()

    def _write_data(self):
        # Overwrites the existing attribute values with the iterable of values provided.
        plist = plistlib.dumps(self.data, fmt=FMT_BINARY)
        self._attrs.set(self._constant, plist)

    def __repr__(self):
        # return f"{type(self).__name__}({super().__repr__()})"
        self._load_data()
        return repr(self.data)

    def __eq__(self, other):
        self._load_data()
        return self.data == other


class _AttributeTagsList(_AttributeList):
    """ represents a _kMDItemUserTag attribute list """

    def set_value(self, value):
        if isinstance(value, list):
            # a list of tag objects
            for val in value:
                if not isinstance(val, Tag):
                    raise TypeError(f"values must be type Tag, not {type(val)}")
            self.data = value
        elif isinstance(value, _AttributeTagsList):
            # another _AttributeTagsList object
            self.data = value.data
        else:
            raise TypeError(f"value must be list of Tag objects not {type(value)}")

        self._write_data()

    def _tag_split(self, tag):
        # Extracts the color information from a Finder tag.

        parts = tag.rsplit("\n", 1)
        if len(parts) == 1:
            return parts[0], 0
        elif (
            len(parts[1]) != 1 or parts[1] not in _VALID_COLORIDS
        ):  # Not a color number
            return tag, 0
        else:
            return parts[0], int(parts[1])

    def _load_data(self):
        self._tags = {}
        try:
            tag_constant = self._attrs[self._constant]
            # load the binary plist value
            self._tagvalues = plistlib.loads(tag_constant)
            for x in self._tagvalues:
                (tag, color) = self._tag_split(x)
                self._tags[tag] = color
        except KeyError:
            self._tags = None
        if self._tags:
            self.data = [Tag(name, color) for name, color in self._tags.items()]
        else:
            self.data = []

        # check color tag stored in com.apple.FinderInfo
        color = get_finderinfo_color(str(self._md._fname))
        if color and (self._tags is None or color not in self._tags.values()):
            # have a FinderInfo color that's not in _kMDItemUserTag
            self.data.append(Tag(_COLORIDS[color], color))

    def _write_data(self):
        # Overwrites the existing attribute values with the iterable of values provided.
        # TODO: _write_data can get called multiple times
        # e.g. md.tags += [Tag("foo", 0)] will result in
        # append --> insert --> __setattr__ --> set_attribute --> set_value
        # which results in _write_data being called twice in a row
        logging.debug(f"_write_data: {self.data}")
        self._tagvalues = [tag._format() for tag in self.data]
        logging.debug(f"_write: {self._tagvalues}")
        plist = plistlib.dumps(self._tagvalues, fmt=FMT_BINARY)
        self._attrs.set(self._constant, plist)

        # also write FinderInfo if required
        # if findercolor in tag set being written, do nothing
        # if findercolor not in tag set being written, overwrite findercolor with first color tag
        finder_color = get_finderinfo_color(str(self._md._fname))
        tag_colors = [tag.color for tag in self.data]
        logging.debug(f"write_data: finder {finder_color}, tag: {tag_colors}")
        if finder_color not in tag_colors:
            # overwrite FinderInfo color with new color
            # get first non-zero color in tag if there is one
            try:
                color = tag_colors[
                    tag_colors.index(
                        next(filter(lambda x: x != FINDER_COLOR_NONE, tag_colors))
                    )
                ]
            except StopIteration:
                color = FINDER_COLOR_NONE
            set_finderinfo_color(str(self._md._fname), color)


class _AttributeFinderInfo:
    """ represents a com.apple.FinderInfo color tag """

    def __init__(self, attribute, xattr_, osxmetadata_obj):
        """ initialize object
            attribute: an OSXMetaData Attributes namedtuple 
            xattr_: an instance of xattr.xattr
            osxmetadata_obj: instance of OSXMetaData that created this class instance """
        self._attribute = attribute
        self._attrs = xattr_
        self._md = osxmetadata_obj

        self._constant = attribute.constant

        self.data = None
        self._load_data()

    def set_value(self, value):
        if isinstance(value, Tag):
            self.data = value
        elif isinstance(value, _AttributeFinderInfo):
            self.data = value.data
        else:
            raise TypeError(f"value must be type Tag, not {type(value)}")

        self._write_data()

    def _load_data(self):
        self._tags = {}

        # check color tag stored in com.apple.FinderInfo
        color = get_finderinfo_color(str(self._md._fname))
        logging.debug(f"AttributeFinderInfo: color = {color}")

        if color is not None:
            # have a FinderInfo color
            self.data = Tag(_COLORIDS[color], color)
            logging.debug(self.data)
        else:
            self.data = None

    def _write_data(self):
        # Overwrites the existing attribute values with the iterable of values provided.
        # TODO: _write_data can get called multiple times
        # e.g. md.tags += [Tag("foo", 0)] will result in
        # append --> insert --> __setattr__ --> set_attribute --> set_value
        # which results in _write_data being called twice in a row

        if self.data is None:
            # nothing to do
            logging.debug(f"No data to write")
            return

        colorid = self.data.color
        if not (_MIN_FINDER_COLOR <= colorid <= _MAX_FINDER_COLOR):
            raise ValueError(f"Invalid color id: {colorid}")
        set_finderinfo_color(str(self._md._fname), colorid)

    def __repr__(self):
        self._load_data()
        return repr(self.data)

    def __str__(self):
        self._load_data()
        return f"'{self.data},{self.data}'"

    def __eq__(self, other):
        self._load_data()
        return self.data == other
