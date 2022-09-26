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

Tag = namedtuple("Tag", ["name", "color"])


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
        tag_data = xattr_obj["com.apple.metadata:_kMDItemUserTags"]
        # load the binary plist values
        tag_values = plistlib.loads(tag_data)
        tags = split_tag_names_colors(tag_values)
    except KeyError:
        tags = []
    return tags
