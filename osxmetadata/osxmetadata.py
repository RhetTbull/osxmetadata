""" OSXMetaData class to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """

# TODO: Add get_xattr(), set_xattr() methods and ability to specify type=bplist

import pathlib
import plistlib
import typing as t

import CoreServices
import xattr
from Foundation import NSURL, NSURLTagNamesKey

from .attribute_data import (
    MDITEM_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_SHORT_NAMES,
    NSURL_RESOURCE_KEY_DATA,
)
from .finder_comment import (
    kMDItemFinderComment,
    set_finder_comment,
)
from .finder_tags import Tag, _kMDItemUserTags, get_finder_tags, set_finder_tags
from .mditem import (
    MDItemValueType,
    get_mditem_metadata,
    set_mditem_metadata,
    remove_mditem_metadata,
)
from .nsurl_metadata import get_nsurl_metadata, set_nsurl_metadata


class OSXMetaData:
    """Create an OSXMetaData object to access file metadata"""

    def __init__(self, fname: str, tz_aware: bool = False):
        """Create an OSXMetaData object to access file metadata
        fname: filename to operate on
        TODO: tz_aware: bool; if True, date/time attributes will return timezone aware datetime.datetime attributes otherwise values will be naive
        """
        self._fname = pathlib.Path(fname)
        if not self._fname.exists():
            raise FileNotFoundError(f"file does not exist: {fname}")

        self._posix_path = self._fname.resolve().as_posix()
        self._tz_aware = tz_aware

        # create MDItemRef, NSURL, and xattr objects
        # MDItemRef is used for most attributes
        # NSURL and xattr are required for certain attributes like Finder tags
        self._mditem: CoreServices.MDItemRef = CoreServices.MDItemCreate(
            None, self._posix_path
        )
        if not self._mditem:
            raise OSError(f"Unable to create MDItem for file: {fname}")
        self._url = NSURL.fileURLWithPath_(self._posix_path)
        self._xattr = xattr.xattr(self._posix_path)

        # Required so __setattr__ gets handled correctly during __init__
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

    def get_xattr(self, key: str, plist: bool = False) -> t.Any:
        """Get xattr value

        Args:
            key: xattr name
            type_: xattr type; if None, return bytes, otherwise return dict
        """
        xattr = self._xattr[key]
        if plist:
            # todo: handle differnet types like datetime and tzaware
            xattr = plistlib.loads(xattr)
        return xattr

    def __getattr__(self, attribute: str) -> MDItemValueType:
        """Get metadata attribute value

        Args:
            attribute: metadata attribute name
        """
        if attribute in ["tags", _kMDItemUserTags]:
            return get_finder_tags(self._xattr)
        elif attribute in MDITEM_ATTRIBUTE_SHORT_NAMES:
            # handle dynamic properties like self.keywords and self.comments
            return get_mditem_metadata(
                self._mditem, MDITEM_ATTRIBUTE_SHORT_NAMES[attribute]
            )
        elif attribute in MDITEM_ATTRIBUTE_DATA:
            return get_mditem_metadata(self._mditem, attribute)
        elif attribute in NSURL_RESOURCE_KEY_DATA:
            return get_nsurl_metadata(self._url, attribute)
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
                if attribute in ["findercomment", kMDItemFinderComment]:
                    # finder comment cannot be set using MDItemSetAttribute
                    if value:
                        set_finder_comment(self._url, value)
                    else:
                        # Note: this does not exactly match the behavior of the Finder
                        # When removing a comment in Finder, a subsequent read of kMDItemFinderComment
                        # returns None (null in objc) but with this code, reading kMDItemFinderComment returns
                        # an empty string; I've not figured out how to mirror the Finder behavior
                        # attempting to set or remove kMDItemFinderComment directly has no effect
                        # The Finder does remove the extended attribute com.apple.metadata:kMDItemFinderComment
                        # so that is what this code does
                        set_finder_comment(self._url, "")
                        self._xattr.remove("com.apple.metadata:kMDItemFinderComment")
                elif attribute in ["tags", _kMDItemUserTags, NSURLTagNamesKey]:
                    # handle Finder tags
                    set_finder_tags(self._url, value)
                elif attribute in MDITEM_ATTRIBUTE_SHORT_NAMES:
                    # handle dynamic properties like self.keywords and self.comments
                    attribute_name = MDITEM_ATTRIBUTE_SHORT_NAMES[attribute]
                    if value is None:
                        remove_mditem_metadata(self._mditem, attribute_name)
                    else:
                        set_mditem_metadata(self._mditem, attribute_name, value)
                elif attribute in MDITEM_ATTRIBUTE_DATA:
                    if value is None:
                        remove_mditem_metadata(self._mditem, attribute)
                    else:
                        set_mditem_metadata(self._mditem, attribute, value)
                elif attribute in NSURL_RESOURCE_KEY_DATA:
                    set_nsurl_metadata(self._url, attribute, value)
                else:
                    raise ValueError(f"Invalid attribute: {attribute}")
        except (KeyError, AttributeError):
            super().__setattr__(attribute, value)

    def __getitem__(self, key: str) -> MDItemValueType:
        """Get metadata attribute value

        Args:
            key: metadata attribute name
        """
        if key == _kMDItemUserTags:
            return get_finder_tags(self._xattr)
        elif key in MDITEM_ATTRIBUTE_DATA:
            return get_mditem_metadata(self._mditem, key)
        elif key in NSURL_RESOURCE_KEY_DATA:
            return get_nsurl_metadata(self._url, key)
        else:
            raise KeyError(f"Invalid key: {key}")

    def __setitem__(self, key: str, value: t.Any):
        """set metadata attribute value

        Args:
            key: metadata attribute name
            value: value to set
        """
        if key == _kMDItemUserTags:
            set_finder_tags(self._xattr, value)
        elif key == kMDItemFinderComment:
            set_finder_comment(self._url, value)
        elif key in MDITEM_ATTRIBUTE_DATA:
            set_mditem_metadata(self._mditem, key, value)
        elif key in NSURL_RESOURCE_KEY_DATA:
            set_nsurl_metadata(self._url, key, value)
        else:
            raise KeyError(f"Invalid key: {key}")
