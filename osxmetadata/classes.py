""" Classes for metadata attribute types """

import collections.abc
import datetime
import plistlib
from plistlib import FMT_BINARY  # pylint: disable=E0611

from .constants import _COLORNAMES, _VALID_COLORIDS


class _AttributeList(collections.abc.MutableSequence):
    """ represents a multi-valued OSXMetaData attribute list """

    def __init__(self, attribute, xattr_):
        """ initialize object
            attribute: an OSXMetaData Attributes namedtuple 
            xattr_: an instance of xattr.xattr """
        self._attribute = attribute
        self._attrs = xattr_
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
                except TypeError:
                    self.data = set([self._values])
            else:
                self.data = []
        except KeyError:
            self.data = []

    def __delitem__(self, index):
        self.data.__delitem__(index)
        self._write_data()

    def __getitem__(self, index):
        self._load_data()
        return self.data.__getitem__(index)

    def __len__(self):
        return self.data.__len__()

    def __setitem__(self, index, value):
        self.data.__setitem__(index, value)
        self._write_data()
        self._load_data()

    def insert(self, index, value):
        self.data.insert(index, value)
        self._write_data()

    def _write_data(self):
        # Overwrites the existing attribute values with the iterable of values provided.
        plist = plistlib.dumps(self.data, fmt=FMT_BINARY)
        self._attrs.set(self._constant, plist)

    def __repr__(self):
        # return f"{type(self).__name__}({super().__repr__()})"
        return repr(self.data)

    def __eq__(self, other):
        return self.data == other


class _AttributeSet:
    """ represents a multi-valued OSXMetaData attribute set """

    def __init__(self, attribute, xattr_):
        """ initialize object
            attribute: an OSXMetaData Attributes namedtuple 
            xattr_: an instance of xattr.xattr """
        self._attribute = attribute
        self._attrs = xattr_
        self._constant = attribute.constant

        # initialize
        self.data = set()
        self._load_data()

    def set_value(self, values):
        """ set value to values """
        self.data = set(map(self._normalize, values))
        self._write_data()

    def add(self, value):
        """ add a value"""
        self._load_data()
        values = set(map(self._normalize, self.data))
        self.data.add(self._normalize(value))
        self._write_data()

    def update(self, *values):
        """ update data adding any new values in *values """
        self._load_data()
        old_values = set(map(self._normalize, self.data))
        new_values = old_values.union(set(map(self._normalize, values)))
        self.data = new_values
        self._write_data()

    def clear(self):
        """ clear attribute (removes all values) """
        try:
            self._attrs.remove(self._constant)
        except (IOError, OSError):
            pass

    def remove(self, value):
        """ remove a value, raise exception if value does not exist in data set """
        self._load_data()
        values = set(map(self._normalize, self.data))
        values.remove(self._normalize(value))
        self.data = values
        self._write_data()

    def discard(self, value):
        """ remove a value, does not raise exception if value does not exist """
        self._load_data()
        values = set(map(self._normalize, self.data))
        values.discard(self._normalize(value))
        self.data = values
        self._write_data()

    def _load_data(self):
        self._values = []
        try:
            # load the binary plist value
            self._values = plistlib.loads(self._attrs[self._constant])
            if self._values:
                try:
                    self.data = set(self._values)
                except TypeError:
                    self.data = set([self._values])
            else:
                self.data = set()
        except KeyError:
            self.data = set()

    def _write_data(self):
        # TODO: change this to write_data and to read from self.data
        # Overwrites the existing tags with the iterable of tags provided.
        plist = plistlib.dumps(list(map(self._normalize, self.data)), fmt=FMT_BINARY)
        self._attrs.set(self._constant, plist)

    def _normalize(self, value):
        """ processes a value to normalize/transform the value if needed
            override in sublcass if desired (e.g. used _TagsSet) """
        return value

    def __iter__(self):
        self._load_data()
        for value in self.data:
            yield value

    def __len__(self):
        self._load_data()
        return len(self.data)

    def __repr__(self):
        self._load_data()
        return repr(self.data)

    def __str__(self):
        self._load_data()
        if self._attribute.type_ == datetime.datetime:
            values = [d.isoformat() for d in self.data]
        else:
            values = self.data
        return str(list(values))

    def __iadd__(self, value):
        for v in value:
            self.add(v)
        return self


class _AttributeTagsSet(_AttributeSet):
    """ represents a _kMDItemUserTag attribute set """

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

    def _normalize(self, tag):
        """
        Ensures a color is set if not none.
        :param tag: a possibly non-normal tag.
        :return: A colorized tag.
        """
        tag, color = self._tag_split(tag)
        if tag.title() in _COLORNAMES:
            # ignore the color passed and set proper color name
            return self._tag_colored(tag.title(), _COLORNAMES[tag.title()])
        else:
            return self._tag_colored(tag, color)

    def _tag_nocolor(self, tag):
        """
        Removes the color information from a Finder tag.
        """
        return tag.rsplit("\n", 1)[0]

    def _tag_colored(self, tag, color):
        """
        Sets the color of a tag.

        Parameters:
        tag(str): a tag name
        color(int): an integer from 1 through 7

        Return:
        (str) the tag with encoded color.
        """
        return "{}\n{}".format(self._tag_nocolor(tag), color)

    def _load_data(self):
        self._tags = {}
        try:
            self._tagvalues = self._attrs[self._constant]
            # load the binary plist value
            self._tagvalues = plistlib.loads(self._tagvalues)
            for x in self._tagvalues:
                (tag, color) = self._tag_split(x)
                self._tags[tag] = color
        except KeyError:
            self._tags = None
        if self._tags:
            self.data = set(self._tags.keys())
        else:
            self.data = set()
