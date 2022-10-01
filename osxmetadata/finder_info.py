"""Read/write metadata in the com.apple.FinderInfo extended attribute such as Stationary Pad

FinderInfo is a 256-bit bit field

For more information see: 
https://eclecticlight.co/2017/12/19/xattr-com-apple-finderinfo-information-for-the-finder/
"""

import bitstring
import xattr

_kFinderInfo = "com.apple.FinderInfo"
_kFinderStationaryPad = "stationarypad"

# offset of tag color in com.apple.FinderInfo xattr
# tag color is 3 bits
_kCOLOR_OFFSET = 76

# offset of stationary pad bit in com.apple.FinderInfo xattr
_kSTATIONARYPAD_OFFSET = 68

__all__ = [
    "get_finderinfo_stationarypad",
    "set_finderinfo_stationarypad",
    "_kFinderStationaryPad",
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


def _set_findinfo_bits(xattr_: xattr.xattr, bits: bitstring.BitArray):
    """Set FinderInfo bits"""
    xattr_.set("com.apple.FinderInfo", bits.bytes)


def get_finderinfo_stationarypad(xattr_: xattr.xattr) -> bool:
    """get the Stationary Pad bit from com.apple.FinderInfo
    returns: True if Stationary Pad is set, False if not set"""

    try:
        finderbits = _get_finderinfo_bits(xattr_)
        bit = finderbits.bin[_kSTATIONARYPAD_OFFSET]
        return bool(int(bit))
    except Exception as e:
        return False


def set_finderinfo_stationarypad(xattr_: xattr.xattr, value: bool):
    """set the Stationary Pad flag of com.apple.FinderInfo"""

    value = 1 if value else 0

    # stationary pad is encoded as a single bit
    bit = bitstring.BitArray(uint=value, length=1)

    # set stationary bits
    finderbits = _get_finderinfo_bits(xattr_)
    finderbits.overwrite(bit, _kSTATIONARYPAD_OFFSET)
    _set_findinfo_bits(xattr_, finderbits)
