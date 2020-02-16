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
    "authors": Attribute(
        "authors", "com.apple.metadata:kMDItemAuthors", str, True, False
    ),
    "creator": Attribute(
        "creator", "com.apple.metadata:kMDItemCreator", str, False, False
    ),
    "description": Attribute(
        "description", "com.apple.metadata:kMDItemDescription", str, False, False
    ),
    "downloadeddate": Attribute(
        "downloadeddate",
        "com.apple.metadata:kMDItemDownloadedDate",
        datetime.datetime,
        False,
        True,
    ),
    "findercomment": Attribute(
        "findercomment", "com.apple.metadata:kMDItemFinderComment", str, False, False
    ),
    "headline": Attribute(
        "headline", "com.apple.metadata:kMDItemHeadline", str, False, False
    ),
    "keywords": Attribute(
        "keywords", "com.apple.metadata:kMDItemKeywords", str, True, False
    ),
    "tags": Attribute("tags", "com.apple.metadata:_kMDItemUserTags", str, True, False),
    "wherefroms": Attribute(
        "wherefroms", "com.apple.metadata:kMDItemWhereFroms", str, True, False
    ),
}

# used for formatting output of --list
_SHORT_NAME_WIDTH = max([len(x) for x in ATTRIBUTES.keys()]) + 5
_LONG_NAME_WIDTH = max([len(x.constant) for x in ATTRIBUTES.values()]) + 10

# also add entries for attributes by constant, do this after computing widths above
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
_TAGS_NAMES = ["tags", "com.apple.metadata:_kMDItemUserTags"]

# list of all attributes for help text
ATTRIBUTES_LIST = [f"{'Short Name':16} Long Name"]
ATTRIBUTES_LIST.extend([f"{a.name:16} {a.constant}" for a in ATTRIBUTES.values()])
