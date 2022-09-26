""" OSXMetaData class to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """

import pathlib
import typing as t

import CoreServices
import xattr
from Foundation import NSURL, NSURLTagNamesKey

from .attribute_data import ATTRIBUTE_DATA, ATTRIBUTE_SHORT_NAMES, RESOURCE_KEY_DATA
from .finder_tags import Tag, _kMDItemUserTags, get_finder_tags, set_finder_tags
from .mditem import MDItemValueType, get_mditem_metadata, set_mditem_metadata
from .nsurl_metadata import get_nsurl_metadata, set_nsurl_metadata


class OSXMetaData:
    """Create an OSXMetaData object to access file metadata"""

    def __init__(self, fname: str, tz_aware: bool = False):
        """Create an OSXMetaData object to access file metadata
        fname: filename to operate on
        tz_aware: bool; if True, date/time attributes will return timezone aware datetime.datetime attributes otherwise values will be naive
        """
        self._fname = pathlib.Path(fname)
        if not self._fname.exists():
            raise FileNotFoundError(f"file does not exist: {fname}")

        self._posix_name = self._fname.resolve().as_posix()
        self._tz_aware = tz_aware

        # create MDItemRef, NSURL, and xattr objects
        # MDItemRef is used for most attributes
        # NSURL and xattr are required for certain attributes like Finder tags
        self._mditem: CoreServices.MDItemRef = CoreServices.MDItemCreate(
            None, self._posix_name
        )
        if not self._mditem:
            raise OSError(f"Unable to create MDItem for file: {fname}")
        self._url = NSURL.fileURLWithPath_(self._posix_name)
        self._xattr = xattr.xattr(self._posix_name)

        # Required so __setattr__ doesn't get called during __init__
        self.__init = True

    def get(self, attribute: str) -> MDItemValueType:
        """Get metadata attribute value
        attribute: metadata attribute name
        """
        return self.__getattr__(attribute)

    def set(self, attribute: str, value: MDItemValueType):
        """Set metadata attribute value

        Args:
            attribute: metadata attribute name
            value: value to set attribute to; must match the type expected by the attribute (e.g. str or list)
        """
        self.__setattr__(attribute, value)

    @property
    def tags(self) -> t.List[Tag]:
        """Get Finder tags"""
        # Note: setter is handled by __setattr__
        return get_finder_tags(self._xattr)

    def __getattr__(self, attribute: str) -> MDItemValueType:
        """Get metadata attribute value

        Args:
            attribute: metadata attribute name
        """
        if attribute in ATTRIBUTE_SHORT_NAMES:
            # handle dynamic properties like self.keywords and self.comments
            return get_mditem_metadata(self._mditem, ATTRIBUTE_SHORT_NAMES[attribute])
        else:
            raise AttributeError(f"Invalid attribute: {attribute}")

    def __setattr__(self, attribute: str, value: t.Any):
        """set metadata attribute value

        Args:
            attribute: metadata attribute name
            value: value to set
        """
        try:
            if self.__init:
                if attribute in ATTRIBUTE_SHORT_NAMES:
                    # handle dynamic properties like self.keywords and self.comments
                    set_mditem_metadata(
                        self._mditem, ATTRIBUTE_SHORT_NAMES[attribute], value
                    )
                elif attribute == "tags":
                    # handle Finder tags
                    set_finder_tags(self._url, value)
        except (KeyError, AttributeError):
            super().__setattr__(attribute, value)

    def __getitem__(self, key: str) -> MDItemValueType:
        """Get metadata attribute value

        Args:
            key: metadata attribute name
        """
        if key in ATTRIBUTE_DATA:
            return get_mditem_metadata(self._mditem, key)
        elif key in RESOURCE_KEY_DATA:
            return get_nsurl_metadata(self._url, key)
        elif key == _kMDItemUserTags:
            return get_finder_tags(self._xattr)
        else:
            raise KeyError(f"Invalid key: {key}")

    def __setitem__(self, key: str, value: t.Any):
        """set metadata attribute value

        Args:
            key: metadata attribute name
            value: value to set
        """
        if key in ATTRIBUTE_DATA:
            set_mditem_metadata(self._mditem, key, value)
        elif key in RESOURCE_KEY_DATA:
            # todo: check read-only in description
            set_nsurl_metadata(self._url, key, value)
        elif key == _kMDItemUserTags:
            set_finder_tags(self._xattr, value)
        else:
            raise KeyError(f"Invalid key: {key}")
