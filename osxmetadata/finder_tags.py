"""Read _kMDItemUserTags (Finder tags) from extended attributes on a file.

Finder tags can be read/written with [NSURL getResourceValue:forKey:error:] and 
[NSURL setResourceValue:forKey:error:] using key NSURLTagNamesKey for tags and
NSURLLabelNumberKey for color (label) number. However, when a tag has a custom color,
only the tag name is returned by NSURLTagNamesKey and NSURLLabelNumberKey does not 
return the color of the custom tag. To get the color of a custom tag, you must read
the extended attribute _kMDItemUserTags. This module reads the extended attribute.
"""

import plistlib
import typing as t
from collections import namedtuple

import xattr
from Foundation import NSURL

from .constants import _COLORIDS, _COLORNAMES_LOWER, _MAX_FINDER_COLOR
from .nsurl_metadata import set_nsurl_metadata

NSURLTagNamesKey = "NSURLTagNamesKey"

Tag = namedtuple("Tag", ["name", "color"])

_kMDItemUserTags = "_kMDItemUserTags"
_kMDItemUserTagsXattr = "com.apple.metadata:_kMDItemUserTags"

__all__ = ["Tag", "_kMDItemUserTags", "get_finder_tags", "set_finder_tags"]


def split_tag_names_colors(tag_values: t.List[str]) -> t.List[Tag]:
    """Split tag name and color from tag value

    Args:
        tag_values: list of tag values

    Returns:
        list of Tag namedtuples
    """
    # tags are in format name\ncolor where color is an int 0-7
    # for example "Blue\n4"
    # I've seen custom tags that have more than one color in the color field though this shouldn't happen
    # so we'll just take the first color
    tags = []
    for tag_value in tag_values:
        tag_data = tag_value.split("\n")
        tag_name = tag_data[0]
        tag_color = int(tag_data[1]) if len(tag_data) > 1 else 0
        tags.append(Tag(tag_name, tag_color))
    return tags


def get_finder_tags(xattr_obj: xattr.xattr) -> t.List[Tag]:
    """Get Finder tags from extended attribute _kMDItemUserTags

    Args:
        xattr_obj: xattr.xattr object for file

    Returns:
        list of Finder tags
    """
    try:
        tag_data = xattr_obj[_kMDItemUserTagsXattr]
        # load the binary plist values
        tag_values = plistlib.loads(tag_data)
        tags = split_tag_names_colors(tag_values)
    except KeyError:
        tags = []
    return tags


def set_finder_tags(url: NSURL, tags: t.Optional[t.List[Tag]]):
    """Set Finder tags in extended attribute _kMDItemUserTags

    Args:
        url: NSURL for file
        tags: list of Finder tags
    """
    if tags is not None and not isinstance(tags, (list, tuple)):
        raise TypeError("tags must be a list or tuple of Tag namedtuples or None")
    if tags is not None and not all(isinstance(tag, Tag) for tag in tags):
        raise TypeError("tags items must be Tag namedtuples")

    # convert to list of strings in format name\ncolor
    tag_values = [f"{tag.name}\n{tag.color}" for tag in tags] if tags else []
    set_nsurl_metadata(url, NSURLTagNamesKey, tag_values)


def tag_factory(tag_str: str) -> Tag:
    """Creates a Tag namedtuple from a string in format 'name,color'

    Args:
        tag_str: (str) tag value in format: 'name,color' where name is the name of the tag and color specifies the color ID;

    Returns:
        Tag namedtuple

    Notes:
        The comma and color are optional; if not provided Tag will use color assigned in Finder or FINDER_COLOR_NONE if no color
            e.g. tag_factory("foo") -> Tag("foo", 0)
                 tag_factory("test,6") -> Tag("test", 6)
    """

    values = tag_str.split(",")
    if len(values) > 2:
        raise ValueError(f"More than one value found after comma: {tag_str}")
    name = values[0]
    name = name.lstrip().rstrip()

    if len(values) == 1:
        # got name only, check to see if name is also a color and if so assign it
        # TODO: this might not be right/desired in different locale settings
        # but I'm not sure yet how to get the non-English color names used by Finder
        try:
            colorid = _COLORNAMES_LOWER[name.lower()]
            return Tag(_COLORIDS[colorid], colorid)
        except KeyError:
            return Tag(name, 0)
    elif len(values) == 2:
        # got a color, is it a name or number
        color = values[1].lstrip().rstrip().lower()
        try:
            colorid = _COLORNAMES_LOWER[color]
        except KeyError as e:
            colorid = int(color)
            if colorid not in range(_MAX_FINDER_COLOR + 1):
                raise ValueError(
                    f"color must be in range 0 to {_MAX_FINDER_COLOR} inclusive: {colorid}"
                ) from e

        return Tag(name, colorid)
