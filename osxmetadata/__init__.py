""" Python package to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """

from ._version import __version__
from .attributes import ATTRIBUTES
from .constants import (
    _COLORIDS,
    _COLORNAMES,
    _FINDER_COMMENT_NAMES,
    _MAX_FINDERCOMMENT,
    _MAX_WHEREFROM,
    _VALID_COLORIDS,
    FINDER_COLOR_BLUE,
    FINDER_COLOR_GRAY,
    FINDER_COLOR_GREEN,
    FINDER_COLOR_NONE,
    FINDER_COLOR_ORANGE,
    FINDER_COLOR_PURPLE,
    FINDER_COLOR_RED,
    FINDER_COLOR_YELLOW,
    FinderInfo,
    _kMDItemUserTags,
    kMDItemAuthors,
    kMDItemComment,
    kMDItemCopyright,
    kMDItemCreator,
    kMDItemDescription,
    kMDItemDownloadedDate,
    kMDItemFinderComment,
    kMDItemHeadline,
    kMDItemKeywords,
    kMDItemParticipants,
    kMDItemProjects,
    kMDItemStarRating,
    kMDItemUserTags,
    kMDItemVersion,
    kMDItemWhereFroms,
)
from .debug import _debug, _set_debug
from .findertags import (
    Tag,
    # get_finderinfo_color,
    get_tag_color_name,
    # set_finderinfo_color,
)
from .osxmetadata import OSXMetaData
