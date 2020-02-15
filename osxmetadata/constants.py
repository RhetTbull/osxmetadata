import datetime
from collections import namedtuple


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

_TAGS = "com.apple.metadata:_kMDItemUserTags"
_FINDER_COMMENT = "com.apple.metadata:kMDItemFinderComment"
_WHERE_FROM = "com.apple.metadata:kMDItemWhereFroms"
_DOWNLOAD_DATE = "com.apple.metadata:kMDItemDownloadedDate"


### Experimenting with generic method of reading / writing attributes
Attribute = namedtuple("Attribute", ["name", "constant", "type", "list", "as_list"])

ATTRIBUTES = {
    "description": Attribute(
        "description", "com.apple.metadata:kMDItemDescription", str, False, False
    ),
    "tags": Attribute("tags", "com.apple.metadata:_kMDItemUserTags", str, True, False),
    "downloadeddate": Attribute(
        "downloadeddate",
        "com.apple.metadata:kMDItemDownloadedDate",
        datetime.datetime,
        False,
        True,
    ),
    "wherefroms": Attribute(
        "wherefroms", "com.apple.metadata:kMDItemWhereFroms", str, True, False
    ),
    "findercomment": Attribute(
        "findercomment", "com.apple.metadata:kMDItemFinderComment", str, False, False
    ),
    "keywords": Attribute(
        "keywords", "com.apple.metadata:kMDItemKeywords", str, True, False
    ),
    "creator": Attribute(
        "creator", "com.apple.metadata:kMDItemCreator", str, False, False
    ),
}


# also add entries for attributes by constant
_temp_attributes = {}
for attribute in ATTRIBUTES.values():
    if attribute.constant not in ATTRIBUTES:
        _temp_attributes[attribute.constant] = attribute
    else:
        raise ValueError(f"Duplicate attribute in ATTRIBUTES: {attribute}")
if _temp_attributes:
    ATTRIBUTES.update(_temp_attributes)

# Special handling for Finder comments
_FINDER_COMMENT_NAMES = ["findercomment", "com.apple.metadata:kMDItemFinderComment"]
