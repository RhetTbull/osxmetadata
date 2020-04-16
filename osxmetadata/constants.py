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


# Special handling for Finder comments
_FINDER_COMMENT_NAMES = [
    "findercomment",
    "kMDItemFinderComment",
    "com.apple.metadata:kMDItemFinderComment",
]
_TAGS_NAMES = ["tags", "com.apple.metadata:_kMDItemUserTags"]

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
]
