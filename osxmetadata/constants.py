""" Constants and definitions used by osxmetadata """

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

_VALID_COLORIDS = "01234567"
_MAX_FINDERCOMMENT = 750  # determined through trial & error with Finder
_MAX_WHEREFROM = (
    1024
)  # just picked something....todo: need to figure out what max length is

# _TAGS = "com.apple.metadata:_kMDItemUserTags"
# _FINDER_COMMENT = "com.apple.metadata:kMDItemFinderComment"
# _WHERE_FROM = "com.apple.metadata:kMDItemWhereFroms"
# _DOWNLOAD_DATE = "com.apple.metadata:kMDItemDownloadedDate"


kMDItemAuthors = "com.apple.metadata:kMDItemAuthors"
kMDItemComment = "com.apple.metadata:kMDItemComment"
kMDItemCopyright = "com.apple.metadata:kMDItemCopyright"
kMDItemCreator = "com.apple.metadata:kMDItemCreator"
kMDItemDescription = "com.apple.metadata:kMDItemDescription"
kMDItemDownloadedDate = "com.apple.metadata:kMDItemDownloadedDate"
kMDItemFinderComment = "com.apple.metadata:kMDItemFinderComment"
kMDItemHeadline = "com.apple.metadata:kMDItemHeadline"
kMDItemKeywords = "com.apple.metadata:kMDItemKeywords"
_kMDItemUserTags = "com.apple.metadata:_kMDItemUserTags"
kMDItemUserTags = "com.apple.metadata:_kMDItemUserTags"
kMDItemWhereFroms = "com.apple.metadata:kMDItemWhereFroms"
FinderInfo = "com.apple.FinderInfo"


# Special handling for Finder comments
_FINDER_COMMENT_NAMES = [
    "findercomment",
    "kMDItemFinderComment",
    "com.apple.metadata:kMDItemFinderComment",
]
_TAGS_NAMES = ["tags", "_kMDItemUserTags", "com.apple.metadata:_kMDItemUserTags"]
_FINDERINFO_NAMES = ["finderinfo", "com.apple.FinderInfo"]

_BACKUP_FILENAME = ".osxmetadata.json"

__all__ = [
    "kMDItemAuthors",
    "kMDItemComment",
    "kMDItemCopyright",
    "kMDItemCreator",
    "kMDItemDescription",
    "kMDItemDownloadedDate",
    "kMDItemFinderComment",
    "kMDItemHeadline",
    "kMDItemKeywords",
    "kMDItemUserTags",
    "_kMDItemUserTags",
    "kMDItemWhereFroms",
    "FinderInfo",
]
