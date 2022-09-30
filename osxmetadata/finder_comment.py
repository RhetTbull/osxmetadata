"""Set Finder comments on a file.

Finder comments can be read by reading the kMDItemFinderComment attribute 
with MDItemCopyAttribute() but they cannot be set with MDItemSetAttribute() so
this script uses Scripting Bridge to get the Finder to set the comment.

It's a bit of a hack but it works and will have to suffice until I can find whatever
undocumented API Finder actually uses to set the comment.
"""


import objc
from Foundation import NSURL
from ScriptingBridge import SBApplication

kMDItemFinderComment = "kMDItemFinderComment"

__all__ = ["set_finder_comment", "kMDItemFinderComment"]


def set_finder_comment(url: NSURL, comment: str):
    """Set Finder comment for file at url"""

    with objc.autorelease_pool():
        finder_app = SBApplication.applicationWithBundleIdentifier_("com.apple.finder")
        if not finder_app:
            raise OSError("Could not instantiate scripting bridge to Finder")

        item = finder_app.items().objectAtLocation_(url)
        item.setComment_(comment)
