"""Get and set macOS metadata keys for NSURL objects, for example, tags and labels"""

import typing as t

import CoreFoundation
import objc
from Foundation import NSURL


__all__ = ["get_nsurl_metadata", "set_nsurl_metadata"]


def get_nsurl_metadata(url: NSURL, key: str) -> t.Any:
    """Get metadata attribute value

    Args:
        key: metadata attribute name, e.g. NSURLTagNamesKey
    """
    success, value, error = url.getResourceValue_forKey_error_(None, key, None)
    if not success:
        raise ValueError(f"Error getting metadata for {key}: {error}")
    return value


def set_nsurl_metadata(url: NSURL, key: str, value: t.Any):
    """Set metadata attribute value

    Args:
        key: metadata attribute name, e.g. NSURLTagNamesKey
        value: value to set attribute to; must match the type expected by the attribute (e.g. str or list)
    """
    with objc.autorelease_pool():
        if isinstance(value, list):
            value = CoreFoundation.CFArrayCreate(
                None, value, len(value), CoreFoundation.kCFTypeArrayCallBacks
            )
        kv = CoreFoundation.NSDictionary.dictionaryWithObject_forKey_(value, key)
        success, error = url.setResourceValues_error_(kv, None)
        if not success:
            raise OSError(f"Error setting tag {key} = {value} on {url}: {error}")
        return True
