""" Classes for metadata attribute types """

import collections.abc
import datetime
import plistlib
from plistlib import FMT_BINARY  # pylint: disable=E0611

import bitstring

from .constants import (
    _COLORIDS,
    _COLORNAMES,
    _COLORNAMES_LOWER,
    _MAX_FINDER_COLOR,
    _MIN_FINDER_COLOR,
    _VALID_COLORIDS,
    FINDER_COLOR_NONE,
    _kCOLOR_OFFSET,
)
from .datetime_utils import (
    datetime_naive_to_utc,
    datetime_remove_tz,
    datetime_utc_to_local,
)
from .debug import _debug
from .findertags import Tag


class _AttributeList(collections.abc.MutableSequence):
    """represents a multi-valued OSXMetaData attribute list"""

    def __init__(self, attribute, xattr_, osxmetadata_obj):
        """initialize object
        attribute: an OSXMetaData Attributes namedtuple
        xattr_: an instance of xattr.xattr
        osxmetadata_obj: instance of OSXMetaData that created this class instance"""
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

    def get_value(self):
        self._load_data()
        return self.data

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


class _AttributeFinderInfo:
    """represents info stored in com.apple.FinderInfo"""

    @classmethod
    def _str_to_value_dict(cls, value):
        """Convert str in format key1:value1,key2:value2, etc to a dict"""
        if value:
            value = value.split(",")
            value = [v.split(":") for v in value]
            value = {k: v for k, v in value}
        else:
            value = {}

        if "color" in value:
            try:
                color = int(value["color"])
            except ValueError:
                color = _COLORNAMES_LOWER[value["color"].lower()]
            value["color"] = color

        return value

    def __init__(self, attribute, xattr_, osxmetadata_obj):
        """initialize object
        attribute: an OSXMetaData Attributes namedtuple
        xattr_: an instance of xattr.xattr
        osxmetadata_obj: instance of OSXMetaData that created this class instance"""

        self._attribute = attribute
        self._attrs = xattr_
        self._md = osxmetadata_obj

        # valid keys for the finderinfo dict
        self.keys = ["color"]

        self._constant = attribute.constant

        self.data = None
        self._load_data()

    def set_value(self, value):
        if not isinstance(value, dict):
            raise TypeError(f"value must be a dict, not {type(value)}")

        if any(key not in self.keys for key in value):
            raise ValueError(f"invalid value dict: value may only contain {self.keys}")

        self.data = value
        self._write_data()

    def get_value(self):
        self._load_data()
        return self.data

    def _load_data(self):
        self._tags = {}

        # check color tag stored in com.apple.FinderInfo
        color = self.get_finderinfo_color()

        self.data = {"color": color}

    def _write_data(self):
        # Overwrites the existing attribute values with the iterable of values provided.
        # TODO: _write_data can get called multiple times
        # e.g. md.tags += [Tag("foo", 0)] will result in
        # append --> insert --> __setattr__ --> set_attribute --> set_value
        # which results in _write_data being called twice in a row

        if self.data is None:
            # nothing to do
            return

        colorid = self.data["color"] if "color" in self.data else FINDER_COLOR_NONE
        self.set_finderinfo_color(colorid)

    @property
    def color(self):
        self._load_data()
        return self.data["color"]

    @color.setter
    def color(self, value):
        self.set_finderinfo_color(value)

    def asdict(self):
        return self.data

    def set_finderinfo_color(self, colorid):
        """set tag color of filename to colorid
        filename: path to file
        colorid: ID of tag color in range 0 to 7
        """

        if colorid is None:
            colorid = FINDER_COLOR_NONE

        if not _MIN_FINDER_COLOR <= colorid <= _MAX_FINDER_COLOR:
            raise ValueError(f"colorid out of range {colorid}")

        # color is encoded as 3 binary bits
        bits = bitstring.BitArray(uint=colorid, length=3)

        # set color bits
        finderbits = self._get_finderinfo_bits()
        finderbits.overwrite(bits, _kCOLOR_OFFSET)
        self._set_findinfo_bits(finderbits)

    def get_finderinfo_color(self):
        """get the tag color of a file set via com.apple.FinderInfo
        filename: path to file
        returns: color id as int, 0 if no color
                or None if com.apple.FinderInfo not set"""

        try:
            finderbits = self._get_finderinfo_bits()
            bits = finderbits[_kCOLOR_OFFSET : _kCOLOR_OFFSET + 3]
            return bits.uint
        except Exception as e:
            return None

    def _get_finderinfo_bits(self) -> bitstring.BitArray:
        """Get FinderInfo bits"""

        try:
            finderinfo = self._attrs.get("com.apple.FinderInfo")
            finderbits = bitstring.BitArray(finderinfo)
        except Exception:
            finderbits = bitstring.BitArray(uint=0, length=256)
        return finderbits

    def _set_findinfo_bits(self, bits: bitstring.BitArray):
        """Set FinderInfo bits"""
        self._attrs.set("com.apple.FinderInfo", bits.bytes)

    def __repr__(self):
        self._load_data()
        return repr(self.data)

    def __str__(self):
        self._load_data()
        return f"'{self.data}'"

    def __eq__(self, other):
        self._load_data()
        return self.data == other

    def __getitem__(self, key):
        self._load_data()
        return self.data[key]


class _AttributeFinderColor(_AttributeFinderInfo):
    def __init__(self, attribute, xattr_, osxmetadata_obj):
        super().__init__(attribute, xattr_, osxmetadata_obj)

    def set_value(self, value):
        if not isinstance(value, int):
            raise TypeError(f"value must be a int, not {type(value)}")

        self.data = {"color": value}
        self._write_data()

    def get_value(self):
        self._load_data()
        return self.data.get("color", None)

    def __repr__(self):
        return repr(self.get_value())

    def __eq__(self, other):
        self._load_data()
        return self.data.get("color") == other


class _AttributeTagsList(_AttributeList, _AttributeFinderInfo):
    """represents a _kMDItemUserTag attribute list"""

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
        color = self.get_finderinfo_color()
        if color and (self._tags is None or color not in self._tags.values()):
            # have a FinderInfo color that's not in _kMDItemUserTag
            self.data.append(Tag(_COLORIDS[color], color))

    def _write_data(self):
        # Overwrites the existing attribute values with the iterable of values provided.
        # TODO: _write_data can get called multiple times
        # e.g. md.tags += [Tag("foo", 0)] will result in
        # append --> insert --> __setattr__ --> set_attribute --> set_value
        # which results in _write_data being called twice in a row
        self._tagvalues = [tag._format() for tag in self.data]
        plist = plistlib.dumps(self._tagvalues, fmt=FMT_BINARY)
        self._attrs.set(self._constant, plist)

        # also write FinderInfo if required
        # if findercolor in tag set being written, do nothing
        # if findercolor not in tag set being written, overwrite findercolor with first color tag
        # the behavior of Finder is to set findercolor to the most recently set color but we won't necessarily know that
        finder_color = self.get_finderinfo_color()
        tag_colors = [tag.color for tag in self.data]
        if finder_color == FINDER_COLOR_NONE or finder_color not in tag_colors:
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
            self.set_finderinfo_color(color)
