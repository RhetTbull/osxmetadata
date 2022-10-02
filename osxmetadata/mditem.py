"""Get/Set macOS metadata using MDItem* functions from CoreServices

Background: Apple provides MDItemCopyAttribute to get metadata from files:
https://developer.apple.com/documentation/coreservices/1427080-mditemcopyattribute?language=objc

but does not provide a documented way to set file metadata.

This package uses the undocumented functions MDItemSetAttribute, MDItemRemoveAttribute to do so.
"""

import datetime
import typing as t

import CoreFoundation
import CoreServices
import objc

from .attribute_data import MDITEM_ATTRIBUTE_DATA, MDIMPORTER_ATTRIBUTE_DATA

__all__ = [
    "get_mditem_metadata",
    "remove_mditem_metadata",
    "set_mditem_metadata",
    "set_or_remove_mditem_metadata",
]

# Absolute time in macOS is measured in seconds relative to the absolute reference date of Jan 1 2001 00:00:00 GMT.
# Reference: https://developer.apple.com/documentation/corefoundation/1542812-cfdategetabsolutetime?language=objc
MACOS_TIME_DELTA = (
    datetime.datetime(2001, 1, 1, 0, 0) - datetime.datetime(1970, 1, 1, 0, 0)
).total_seconds()

MDItemValueType = t.Union[bool, str, float, t.List[str], datetime.datetime]

# load undocumented function MDItemSetAttribute
# signature: Boolean MDItemSetAttribute(MDItemRef, CFStringRef name, CFTypeRef attr);
# references:
# https://github.com/WebKit/WebKit/blob/5b8ad34f804c64c944ebe43c02aba88482c2afa8/Source/WTF/wtf/mac/FileSystemMac.MDItemSetAttribute
# https://pyobjc.readthedocs.io/en/latest/metadata/manual.html#objc.loadBundleFunctions
# signature of B@@@ translates to returns BOOL, takes 3 arguments, all objects
# In reality, the function takes references (pointers) to the objects, but pyobjc barfs if
# the function signature is specified using pointers.
# Specifying generic objects allows the bridge to convert the Python objects to the
# appropriate Objective C object pointers.


def MDItemSetAttribute(mditem, name, attr):
    """dummy function definition"""
    ...


def MDItemRemoveAttribute(mditem, name):
    """ "dummy function definition"""
    ...


# This will load MDItemSetAttribute from the CoreServices framework into module globals
objc.loadBundleFunctions(
    CoreServices.__bundle__,
    globals(),
    [("MDItemSetAttribute", b"B@@@"), ("MDItemRemoveAttribute", b"B@@")],
)


def value_to_boolean(value: str) -> bool:
    """Convert string to boolean"""
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    elif value.isdigit():
        return bool(int(value))
    else:
        raise ValueError(f"Invalid boolean value: {value}")


def set_mditem_metadata(
    mditem: CoreServices.MDItemRef,
    attribute: str,
    value: MDItemValueType,
) -> bool:
    """Set file metadata using undocumented function MDItemSetAttribute

    file: path to file
    attribute: metadata attribute to set
    value: value to set attribute to; must match the type expected by the attribute (e.g. bool, str, List[str], float, datetime.datetime)

    Returns True if successful, False otherwise.
    """
    if isinstance(value, list):
        value = CoreFoundation.CFArrayCreate(
            None, value, len(value), CoreFoundation.kCFTypeArrayCallBacks
        )
    elif isinstance(value, datetime.datetime):
        value = CoreFoundation.CFDateCreate(None, value.timestamp() - MACOS_TIME_DELTA)
    return MDItemSetAttribute(
        mditem,
        attribute,
        value,
    )


def get_mditem_metadata(
    mditem: CoreServices.MDItemRef, attribute: str
) -> MDItemValueType:
    """Get file metadata using MDItemCopyAttribute

    mditem: MDItem object
    attribute: metadata attribute to get

    Returns value of attribute
    """
    value = CoreServices.MDItemCopyAttribute(mditem, attribute)
    if value is None:
        return None
    if attribute in MDITEM_ATTRIBUTE_DATA:
        attribute_data = MDITEM_ATTRIBUTE_DATA[attribute]
    elif attribute in MDIMPORTER_ATTRIBUTE_DATA:
        attribute_data = MDIMPORTER_ATTRIBUTE_DATA[attribute]
    else:
        raise ValueError(f"Unknown attribute: {attribute}")

    # Some attributes don't have a documented type
    attribute_type = attribute_data.get("python_type")
    if attribute_type == bool:
        return bool(value)
    elif attribute_type == str:
        return str(value)
    elif attribute_type == float:
        return float(value)
    elif attribute_type == list:
        return [str(x) for x in value]
    elif attribute_type == datetime.datetime:
        return datetime.datetime.fromtimestamp(
            CoreFoundation.CFDateGetAbsoluteTime(value) + MACOS_TIME_DELTA
        )
    elif attribute_type == "list[datetime]":
        return [
            datetime.datetime.fromtimestamp(
                CoreFoundation.CFDateGetAbsoluteTime(x) + MACOS_TIME_DELTA
            )
            for x in value
        ]
    else:
        return value


def remove_mditem_metadata(mditem: CoreServices.MDItemRef, attribute: str):
    """Remove file metadata using undocumented function MDItemRemoveAttribute

    mditem: MDItem object
    attribute: metadata attribute to remove
    """
    MDItemRemoveAttribute(mditem, attribute)


def set_or_remove_mditem_metadata(
    mditem: CoreServices.MDItemRef,
    attribute: str,
    value: MDItemValueType,
) -> bool:
    """Set file metadata or remove metadata if value is None

    file: path to file
    attribute: metadata attribute to set
    value: value to set attribute to; must match the type expected by the attribute (e.g. bool, str, List[str], float, datetime.datetime)

    Returns True if successful, False otherwise.
    """
    if value is None:
        remove_mditem_metadata(mditem, attribute)
    else:
        set_mditem_metadata(mditem, attribute, value)
