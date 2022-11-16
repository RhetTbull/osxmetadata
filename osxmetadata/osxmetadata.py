""" OSXMetaData class to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """

import base64
import datetime
import json
import pathlib
import typing as t

import CoreServices
import xattr
from Foundation import NSURL

from ._version import __version__
from .attribute_data import (
    MDIMPORTER_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_SHORT_NAMES,
    NSURL_RESOURCE_KEY_DATA,
)
from .finder_comment import kMDItemFinderComment, set_or_remove_finder_comment
from .finder_info import (
    _kFinderColor,
    _kFinderInfo,
    _kFinderStationeryPad,
    get_finderinfo_bytes,
    get_finderinfo_color,
    get_finderinfo_stationerypad,
    set_finderinfo_bytes,
    set_finderinfo_color,
    set_finderinfo_stationerypad,
)
from .finder_tags import _kMDItemUserTags, get_finder_tags, set_finder_tags
from .mditem import (
    MDItemValueType,
    get_mditem_metadata,
    set_or_remove_mditem_metadata,
    MDItemSetAttribute,
)
from .nsurl_metadata import get_nsurl_metadata, set_nsurl_metadata

ALL_ATTRIBUTES = {
    "finderinfo",
    "tags",
    *list(MDITEM_ATTRIBUTE_DATA.keys()),
    *list(MDITEM_ATTRIBUTE_SHORT_NAMES.keys()),
    *list(NSURL_RESOURCE_KEY_DATA.keys()),
    *list(MDIMPORTER_ATTRIBUTE_DATA.keys()),
    _kFinderColor,
    _kFinderInfo,
    _kFinderStationeryPad,
    _kMDItemUserTags,
}

# Subset of attributes returned by asdict() and to_json() methods
ASDICT_ATTRIBUTES = {
    *list(MDITEM_ATTRIBUTE_DATA.keys()),
    *list(MDIMPORTER_ATTRIBUTE_DATA.keys()),
    _kFinderStationeryPad,
    _kFinderColor,
    _kMDItemUserTags,
}


class OSXMetaDataAttributeError(Exception):
    """Raised when an attribute is not supported or attempting to set read-only attribute"""

    pass


class OSXMetaData:
    """Create an OSXMetaData object to access file metadata"""

    def __init__(self, fname: str):
        """Create an OSXMetaData object to access file metadata
        fname: filename to operate on
        """
        self._fname = pathlib.Path(fname)
        if not self._fname.exists():
            raise FileNotFoundError(f"file does not exist: {fname}")

        self._posix_path = self._fname.resolve().as_posix()

        # Create MDItemRef, NSURL, and xattr objects
        # MDItemRef is used for most attributes
        # NSURL and xattr are required for certain attributes like Finder tags
        # Because many of the getter/setter functions require some combination of MDItemRef, NSURL, and xattr,
        # they are created here and kept for the life of the object so that they don't have to be
        # recreated for each attribute
        # This does mean that if the file is moved or renamed, the object will still be pointing to the old file
        # thus you should not rename or move a file while using an OSXMetaData object
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

    def get_xattr(
        self, key: str, decode: t.Callable[[t.ByteString], t.Any] = None
    ) -> t.Any:
        """Get xattr value

        Args:
            key: xattr name
            decode: optional Callable to decode value before returning
        """
        xattr = self._xattr[key]
        if decode:
            xattr = decode(xattr)
        return xattr

    def set_xattr(
        self, key: str, value: t.Any, encode: t.Callable[[t.ByteString], t.Any] = None
    ):
        """Set xattr value

        Args:
            key: xattr name
            encode: optional Callable to encode value before setting
        """
        if encode:
            value = encode(value)
        self._xattr[key] = value

    def remove_xattr(self, key: str):
        """Remove xattr

        Args:
            key: xattr name
        """
        self._xattr.remove(key)

    def asdict(self, attributes: t.Set[str] = ASDICT_ATTRIBUTES) -> t.Dict[str, t.Any]:
        """Return all MDItem metadata (or a subset defined by attributes) as a dict

        Args:
            attributes: set of attributes to include in dict

        Returns:
            dict of metadata
        """
        return {key: getattr(self, key) for key in attributes}

    def to_json(
        self, attributes: t.Set[str] = ASDICT_ATTRIBUTES, indent: int = 4
    ) -> str:
        """Return all MDItem metadata (or a subset defined by attributes) as a JSON string

        Args:
            attributes: set of attributes to include in JSON
            indent: indent level for JSON output

        Returns:
            JSON string

        Notes:
            datetime objects are converted to ISO 8601 format
            binary objects are converted to base64 encoded strings
            the resulting JSON will include 3 additional keys: _version, _filepath, and _filename;
            these are expected by the CLI backup/restore commands
        """

        dict_data = self.asdict(attributes)

        # add fields that backup/restore expects
        dict_data.update(
            {
                "_version": __version__,
                "_filepath": self._posix_path,
                "_filename": self._fname.name,
            }
        )

        for key, value in dict_data.items():
            if isinstance(value, datetime.datetime):
                dict_data[key] = value.isoformat()
            elif isinstance(value, (list, tuple)):
                if value and isinstance(value[0], datetime.datetime):
                    dict_data[key] = [v.isoformat() for v in value]
            elif isinstance(value, bytes):
                dict_data[key] = base64.b64encode(value).decode("ascii")

        return json.dumps(dict_data, indent=indent)

    def get_mditem_attribute_value(self, attribute: str) -> t.Any:
        """Get the raw MDItem attribute value without any type conversion.

        Args:
            attribute: metadata attribute name

        Returns:
            raw MDItem attribute value as returned by CoreServices.MDItemCopyAttribute()

        Note: This is a low level function that you probably don't need to use,
        but may be useful in some cases. You should probably use the get() method instead.
        """
        return CoreServices.MDItemCopyAttribute(self._mditem, attribute)

    def set_mditem_attribute_value(self, attribute: str, value: t.Any) -> bool:
        """Set the raw MDItem attribute value without any type conversion.

        Args:
            attribute: metadata attribute name
            value: value to set attribute to

        Returns: True if successful otherwise False

        Note: This is a low level function that you probably don't need to use,
        but may be useful in some cases. You should probably use the set() method instead.
        """
        return MDItemSetAttribute(self._mditem, attribute, value)

    @property
    def path(self) -> str:
        """Return path to file"""
        return self._posix_path

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
        elif (
            attribute in MDITEM_ATTRIBUTE_DATA or attribute in MDIMPORTER_ATTRIBUTE_DATA
        ):
            return get_mditem_metadata(self._mditem, attribute)
        elif attribute in NSURL_RESOURCE_KEY_DATA:
            return get_nsurl_metadata(self._url, attribute)
        elif attribute in ["finderinfo", _kFinderInfo]:
            return get_finderinfo_bytes(self._xattr)
        elif attribute == _kFinderStationeryPad:
            return get_finderinfo_stationerypad(self._xattr)
        elif attribute == _kFinderColor:
            return get_finderinfo_color(self._xattr)
        else:
            raise AttributeError(f"Invalid attribute: {attribute}")

    def __setattr__(self, attribute: str, value: t.Any):
        """set metadata attribute value

        Args:
            attribute: metadata attribute name
            value: value to set
        """
        try:
            if not self.__init:
                # during __init__ we don't want to call __setattr__ as it will
                # cause an infinite loop
                return super().__setattr__(attribute, value)
            if attribute in ["findercomment", kMDItemFinderComment]:
                # finder comment cannot be set using MDItemSetAttribute
                set_or_remove_finder_comment(self._url, self._xattr, value)
            elif attribute in ["tags", _kMDItemUserTags]:
                # handle Finder tags
                set_finder_tags(self._url, value)
            elif attribute in MDITEM_ATTRIBUTE_SHORT_NAMES:
                # handle dynamic properties like self.keywords and self.comments
                attribute_name = MDITEM_ATTRIBUTE_SHORT_NAMES[attribute]
                set_or_remove_mditem_metadata(self._mditem, attribute_name, value)
            elif attribute in MDITEM_ATTRIBUTE_DATA:
                set_or_remove_mditem_metadata(self._mditem, attribute, value)
            elif attribute in NSURL_RESOURCE_KEY_DATA:
                set_nsurl_metadata(self._url, attribute, value)
            elif attribute in ["finderinfo", _kFinderInfo]:
                set_finderinfo_bytes(self._xattr, value)
            elif attribute == _kFinderStationeryPad:
                set_finderinfo_stationerypad(self._xattr, bool(value))
            elif attribute == _kFinderColor:
                set_finderinfo_color(self._xattr, value)
            elif attribute in ALL_ATTRIBUTES:
                raise OSXMetaDataAttributeError(f"Attribute {attribute} is read-only")
            else:
                raise OSXMetaDataAttributeError(f"Invalid attribute: {attribute}")
        except (KeyError, AttributeError):
            super().__setattr__(attribute, value)
        except OSXMetaDataAttributeError as e:
            raise AttributeError(e) from e

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
            set_or_remove_finder_comment(self._url, self._xattr, value)
        elif key in MDITEM_ATTRIBUTE_DATA:
            set_or_remove_mditem_metadata(self._mditem, key, value)
        elif key in NSURL_RESOURCE_KEY_DATA:
            set_nsurl_metadata(self._url, key, value)
        elif key in ALL_ATTRIBUTES:
            raise KeyError(f"Attribute {key} is read-only")
        else:
            raise KeyError(f"Invalid key: {key}")
