""" Constants and definitions used by osxmetadata """

FINDER_COLOR_NONE = 0
FINDER_COLOR_GRAY = 1
FINDER_COLOR_GREEN = 2
FINDER_COLOR_PURPLE = 3
FINDER_COLOR_BLUE = 4
FINDER_COLOR_YELLOW = 5
FINDER_COLOR_RED = 6
FINDER_COLOR_ORANGE = 7

_MIN_FINDER_COLOR = 0
_MAX_FINDER_COLOR = 7

# color labels
_COLORNAMES = {
    "None": 0,
    "Gray": 1,
    "Green": 2,
    "Purple": 3,
    "Blue": 4,
    "Yellow": 5,
    "Red": 6,
    "Orange": 7,
}

_COLORNAMES_LOWER = {
    "none": 0,
    "gray": 1,
    "green": 2,
    "purple": 3,
    "blue": 4,
    "yellow": 5,
    "red": 6,
    "orange": 7,
}

_COLORIDS = {
    0: "None",
    1: "Gray",
    2: "Green",
    3: "Purple",
    4: "Blue",
    5: "Yellow",
    6: "Red",
    7: "Orange",
}

__all__ = [
    "FINDER_COLOR_NONE",
    "FINDER_COLOR_GRAY",
    "FINDER_COLOR_GREEN",
    "FINDER_COLOR_PURPLE",
    "FINDER_COLOR_BLUE",
    "FINDER_COLOR_YELLOW",
    "FINDER_COLOR_RED",
    "FINDER_COLOR_ORANGE",
    "_MIN_FINDER_COLOR",
    "_MAX_FINDER_COLOR",
    "_COLORNAMES",
    "_COLORNAMES_LOWER",
    "_COLORIDS",
]



# _VALID_COLORIDS = "01234567"
# _MAX_FINDERCOMMENT = 750  # determined through trial & error with Finder
# _MAX_WHEREFROM = (
#     1024  # just picked something....todo: need to figure out what max length is
# )


# FinderInfo = "com.apple.FinderInfo"
# _kMDItemUserTags = "com.apple.metadata:_kMDItemUserTags"
# OSXPhotosDetectedText = "osxphotos.metadata:detected_text"

# Special handling for Finder comments
_FINDER_COMMENT_NAMES = [
    "findercomment",
    "kMDItemFinderComment",
    "com.apple.metadata:kMDItemFinderComment",
]
_TAGS_NAMES = ["tags", "_kMDItemUserTags", "com.apple.metadata:_kMDItemUserTags"]


# __all__ = [
#     "FinderInfo",
#     "_kMDItemUserTags",
#     "OSXPhotosDetectedText",
# ]
