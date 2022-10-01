"""Set Finder comments on a file.

Finder comments can be read by reading the kMDItemFinderComment attribute 
with MDItemCopyAttribute() but they cannot be set with MDItemSetAttribute() so
this script uses Scripting Bridge to get the Finder to set the comment.

It's a bit of a hack but it works and will have to suffice until I can find whatever
undocumented API Finder actually uses to set the comment.
"""

import objc
import xattr
from Foundation import NSURL
from ScriptingBridge import SBApplication

kMDItemFinderComment = "kMDItemFinderComment"

__all__ = [
    "clear_finder_comment",
    "kMDItemFinderComment",
    "set_finder_comment",
    "set_or_remove_finder_comment",
]

# _scpt_clear_finder_comment = applescript.AppleScript(
#     """
#         on run {path}
#             tell application "Finder" to set comment of (POSIX file path as alias) to missing value
#         end run
#     """
# )


def set_finder_comment(url: NSURL, comment: str):
    """Set Finder comment for file at url"""

    with objc.autorelease_pool():
        finder_app = SBApplication.applicationWithBundleIdentifier_("com.apple.finder")
        if not finder_app:
            raise OSError("Could not instantiate scripting bridge to Finder")

        item = finder_app.items().objectAtLocation_(url)
        item.setComment_(comment)


def set_or_remove_finder_comment(url: NSURL, xattr_: xattr.xattr, comment: str):
    """Set Finder comment for file at url

    If comment is None, remove the comment
    """
    if comment:
        set_finder_comment(url, comment)
    else:
        # Note: this does not exactly match the behavior of the Finder
        # When removing a comment in Finder, a subsequent read of kMDItemFinderComment
        # returns None (null in objc) but with this code, reading kMDItemFinderComment returns
        # an empty string; I've not figured out how to mirror the Finder behavior
        # attempting to set or remove kMDItemFinderComment directly has no effect
        # The Finder does remove the extended attribute com.apple.metadata:kMDItemFinderComment
        # so that is what this code does
        set_finder_comment(url, "")
        xattr_.remove("com.apple.metadata:kMDItemFinderComment")


# def clear_finder_comment(path: str, xattr_: xattr.xattr):
#     """Clear Finder comment for file at path"""

#     _scpt_clear_finder_comment.run(path)

#     # remove attribute from xattr list
#     # if Finder comment value was None or "", remove the attribute
#     # this mirrors what Finder does when you clear the comment
#     # but the AppleScript/ScriptingBridge interface does not do this
#     xattr_.remove("com.apple.metadata:kMDItemFinderComment")
