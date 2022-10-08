"""Read/write metadata in the com.apple.FinderInfo extended attribute such as Stationery Pad

FinderInfo is a 256-bit bit field

For more information see: 
https://eclecticlight.co/2017/12/19/xattr-com-apple-finderinfo-information-for-the-finder/
"""

import bitstring
import xattr

from .constants import (
    _COLORNAMES_LOWER,
    _MAX_FINDER_COLOR,
    _MIN_FINDER_COLOR,
    FINDER_COLOR_NONE,
)

_kFinderInfo = "com.apple.FinderInfo"
_kFinderStationeryPad = "stationerypad"
_kFinderColor = "findercolor"

# offset of tag color in com.apple.FinderInfo xattr
# tag color is 3 bits
_kCOLOR_OFFSET = 76

# offset of stationery pad bit in com.apple.FinderInfo xattr
_kSTATIONERYPAD_OFFSET = 68

__all__ = [
    "_kFinderColor",
    "_kFinderInfo",
    "_kFinderStationeryPad",
    "get_finderinfo_bytes",
    "get_finderinfo_color",
    "get_finderinfo_stationerypad",
    "set_finderinfo_bytes",
    "set_finderinfo_color",
    "set_finderinfo_stationerypad",
    "str_to_finder_color",
]


def _get_finderinfo_bits(xattr_: xattr.xattr) -> bitstring.BitArray:
    """Get FinderInfo bits"""

    try:
        finderinfo = xattr_.get(_kFinderInfo)
        finderbits = bitstring.BitArray(finderinfo)
    except OSError:
        # if the extended attribute is missing, the error will be
        # OSError: [Errno 93] Attribute not found
        # in this case, create a new bitstring with all bits set to 0
        finderbits = bitstring.BitArray(uint=0, length=256)
    return finderbits


def _set_finderinfo_bits(xattr_: xattr.xattr, bits: bitstring.BitArray):
    """Set FinderInfo bits"""
    xattr_.set("com.apple.FinderInfo", bits.bytes)


def get_finderinfo_bytes(xattr_: xattr.xattr) -> bytes:
    """Get FinderInfo bytes"""
    finderbits = _get_finderinfo_bits(xattr_)
    return finderbits.bytes


def set_finderinfo_bytes(xattr_: xattr.xattr, value: bytes):
    """Set FinderInfo bytes"""
    finderbits = bitstring.BitArray(value)
    _set_finderinfo_bits(xattr_, finderbits)


def get_finderinfo_stationerypad(xattr_: xattr.xattr) -> bool:
    """get the Stationery Pad bit from com.apple.FinderInfo
    returns: True if Stationery Pad is set, False if not set"""

    try:
        finderbits = _get_finderinfo_bits(xattr_)
        bit = finderbits.bin[_kSTATIONERYPAD_OFFSET]
        return bool(int(bit))
    except Exception as e:
        return False


def set_finderinfo_stationerypad(xattr_: xattr.xattr, value: bool):
    """set the Stationery Pad flag of com.apple.FinderInfo"""

    value = 1 if value else 0

    # stationery pad is encoded as a single bit
    bit = bitstring.BitArray(uint=value, length=1)

    # set stationery bits
    finderbits = _get_finderinfo_bits(xattr_)
    finderbits.overwrite(bit, _kSTATIONERYPAD_OFFSET)
    _set_finderinfo_bits(xattr_, finderbits)


def get_finderinfo_color(xattr_: xattr.xattr) -> int:
    """get the tag color of a file set via com.apple.FinderInfo
    Returns: color id as int, 0 if no color or FinderInfo not set"""

    try:
        finderbits = _get_finderinfo_bits(xattr_)
        bits = finderbits[_kCOLOR_OFFSET : _kCOLOR_OFFSET + 3]
        return bits.uint
    except OSError as e:
        # if the extended attribute is missing, the error will be OSError: [Errno 93] Attribute not found
        return 0


def set_finderinfo_color(xattr_: xattr.xattr, colorid: int):
    """set tag color of filename to colorid

    Args:
        colorid: ID of tag color in range 0 to 7
    """

    if colorid is None:
        colorid = FINDER_COLOR_NONE

    if not _MIN_FINDER_COLOR <= colorid <= _MAX_FINDER_COLOR:
        raise ValueError(f"colorid out of range {colorid}")

    # color is encoded as 3 binary bits
    bits = bitstring.BitArray(uint=colorid, length=3)

    # set color bits
    finderbits = _get_finderinfo_bits(xattr_)
    finderbits.overwrite(bits, _kCOLOR_OFFSET)
    _set_finderinfo_bits(xattr_, finderbits)


def str_to_finder_color(color: str) -> int:
    """Convert a string to a Finder color ID

    Args:
        color: string name of color or integer color ID

    Returns:
        int Finder color ID

    Raises:
        ValueError: if color is not a valid color name
    """

    color = color.lower()
    try:
        colorid = int(color)
        if not _MIN_FINDER_COLOR <= colorid <= _MAX_FINDER_COLOR:
            raise ValueError(f"colorid out of range {colorid}")
        return colorid
    except ValueError as e:
        try:
            return _COLORNAMES_LOWER[color]
        except KeyError as e:
            raise ValueError(f"invalid color name {color}") from e
