""" Functions for handling Finder tags and colors """

import logging
import os
import pathlib
import plistlib
import sys

import bitstring
import xattr

from osxmetadata.constants import (
    _COLORIDS,
    _COLORIDS,
    _COLORNAMES,
    _COLORNAMES_LOWER,
    _MAX_FINDER_COLOR,
    _MIN_FINDER_COLOR,
    FINDER_COLOR_NONE,
)

# offset of tag color in com.apple.FinderInfo xattr
# tag color is 3 bits
_kCOLOR_OFFSET = 76


def set_finderinfo_color(filename, colorid):
    """ set tag color of filename to colorid
        filename: path to file
        colorid: ID of tag color in range 0 to 7
    """

    if not os.path.exists(filename):
        raise FileNotFoundError(f"filename {filename} not found")

    if not _MIN_FINDER_COLOR <= colorid <= _MAX_FINDER_COLOR:
        raise ValueError(f"colorid out of range {colorid}")

    attr = xattr.xattr(filename)

    try:
        finderinfo = attr.get("com.apple.FinderInfo")
        finderbits = bitstring.BitArray(finderinfo)
    except:
        finderbits = bitstring.BitArray(uint=0, length=256)

    # color is encoded as 3 binary bits
    bits = bitstring.BitArray(uint=colorid, length=3)

    # set color bits
    finderbits.overwrite(bits, _kCOLOR_OFFSET)
    attr.set("com.apple.FinderInfo", finderbits.bytes)


def get_finderinfo_color(filename):
    """ get the tag color of a file set via com.apple.FinderInfo
        filename: path to file
        returns: color id as int, 0 if no color 
                 or None if com.apple.FinderInfo not set """

    if not os.path.exists(filename):
        raise FileNotFoundError(f"filename {filename} not found")

    attr = xattr.xattr(filename)

    try:
        finderinfo = attr.get("com.apple.FinderInfo")
        finderbits = bitstring.BitArray(finderinfo)
        bits = finderbits[_kCOLOR_OFFSET : _kCOLOR_OFFSET + 3]
        return bits.uint
    except Exception as e:
        logging.debug(f"get_finderinfo_color: {e}")
        return None


def get_tag_color_name(colorid):
    """ Return name of the Finder color based on ID """
    # TODO: need to figure out how to do this in locale/language name
    try:
        colorname = _COLORIDS[colorid]
    except:
        raise ValueError(f"Invalid colorid: {colorid}")
    return colorname


def tag_factory(tag_str):
    """ creates a Tag object
        tag_str: (str) tag value in format: 'name,color' 
        where name is the name of the tag and color specifies the color ID
        the comma and color are optional; 
        if not provided Tag will use color assigned in Finder or FINDER_COLOR_NONE if no color 
        e.g. tag_factory("foo") -> Tag("foo")
             tag_factory("test,6") -> Tag("test", 6) """

    if not isinstance(tag_str, str):
        raise TypeError(f"tag_str must be str not {type(tag_str)}")

    values = tag_str.split(",")
    name = values[0]
    name = name.lstrip().rstrip()
    logging.debug(f"values={values},name={name}")
    if len(values) > 2:
        raise ValueError(f"More than one value found after comma: {tag_str}")
    elif len(values) == 1:
        # got name only, check to see if name is also a color and if so assign it
        # TODO: this might not be right/desired in different locale settings
        # but I'm not sure yet how to get the non-English color names used by Finder
        try:
            colorid = _COLORNAMES_LOWER[name.lower()]
            logging.debug(f"single: values: {values}, colorid: {colorid}")
            return Tag(_COLORIDS[colorid], colorid)
        except KeyError:
            return Tag(name)
    elif len(values) == 2:
        # got a color, is it a name or number
        color = values[1].lstrip().rstrip().lower()
        try:
            colorid = _COLORNAMES_LOWER[color]
            logging.debug(f"values: {values}, color: {color}, colorid: {colorid}")
        except KeyError:
            colorid = int(color)
            if colorid not in range(_MAX_FINDER_COLOR + 1):
                raise ValueError(
                    f"color must be in range 0 to {_MAX_FINDER_COLOR} inclusive: {colorid}"
                )
            logging.debug(f"KeyError: values: {values}, colorid: {colorid}")
        return Tag(name, colorid)


def get_finder_tags():
    """ parses com.apple.finder.plist to get list of Finder tags and associated colors
        returns: dict in form {tag_name: color_id} """

    # TODO: Is it possible to get a race condition where Finder is writing at same time
    # this code is trying to open the plist file?  If so, what happens?
    plist_file = pathlib.Path(
        str(pathlib.Path.home()) + "/Library/SyncedPreferences/com.apple.finder.plist"
    )
    tags = {}
    try:
        with open(plist_file, "rb") as fp:
            pl = plistlib.load(fp)
            try:
                finder_tags = pl["values"]["FinderTagDict"]["value"]["FinderTags"]
                for tag in finder_tags:
                    try:
                        name = tag["n"]
                        color = tag["l"]
                    except KeyError:
                        # color will not be present if no color
                        color = 0
                    tags[name] = color

            except Exception as e:
                logging.warning(f"Exception while parsing plist file: {e}")
                raise e

    except Exception as e:
        logging.warning(f"Could not open plist file: {plist_file}, exception: {e}")
        raise e

    return tags


class Tag:
    """ Information about Finder tags/keywords and associated color labels """

    def __init__(self, name, *color):
        """ Create a new Tag object
            name: (str) name of the tag
            color: (int) color ID of the tag, optional
            If color name is not provided, com.apple.finder.plist will be parsed to see if 
            a color is already associated with 'name' and if so, that color will be assigned
            If a color is provided and the Finder's color is different, a warning will be logged
            but the new color ID will be used """

        # input validation
        # todo: add length validation on name? Need to determine what max tag length is for Finder
        # and if there are any illegal characters
        if type(name) is not str:
            raise TypeError(f"name must be a str not {type(name)}")
        if len(color):
            if len(color) != 1:
                raise ValueError(
                    f"only 1 argument expected for color but {len(color)} provided"
                )
            if type(color[0]) is not int:
                raise TypeError(f"color must be an int not {type(color[0])}")
            if color[0] not in range(_MAX_FINDER_COLOR + 1):
                raise ValueError(
                    f"color must be in range 0 to {_MAX_FINDER_COLOR} inclusive: {color[0]}"
                )

        self._finder_tags = get_finder_tags()
        self._name = name

        # if no color provided use color from Finder if it exists
        if not len(color):
            # no color provided
            if name in self._finder_tags:
                # use color Finder already using
                self._colorid = self._finder_tags[name]
            else:
                self._colorid = FINDER_COLOR_NONE  # set to no color
        elif len(color):
            # color was provided
            if name in self._finder_tags:
                # color in Finder, check to see if colors match
                if color[0] != self._finder_tags[name]:
                    logging.warning(
                        f"assigning color {color[0]} to tag {name} but "
                        f"color {self._finder_tags[name]} already assigned in Finder"
                    )
                self._colorid = color[0]
            else:
                self._colorid = color[0]

    @property
    def name(self):
        return self._name

    @property
    def color(self):
        return self._colorid

    def _format(self):
        """ formats a tag for writing to _kMDItemUserTags """
        return f"{self.name}\n{self.color}"

    def __str__(self):
        return f"{self.name}: {_COLORIDS[self.color]}"

    def __repr__(self):
        return f"Tag('{self.name}', {self.color})"

    def __eq__(self, other):
        return (
            isinstance(other, Tag)
            and self.name == other.name
            and self.color == other.color
        )

    def __lt__(self, other):
        if not isinstance(other, Tag):
            raise TypeError(f"< not supported between type Tag and type {type(other)}")

        return self.name < other.name

    def __gt__(self, other):
        if not isinstance(other, Tag):
            raise TypeError(f"< not supported between type Tag and type {type(other)}")

        return self.name > other.name

    def __len__(self):
        return len(self.name)
