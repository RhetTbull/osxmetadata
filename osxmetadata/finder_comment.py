"""Set Finder comments on a file.

Finder comments can be read by reading the kMDItemFinderComment attribute 
with MDItemCopyAttribute() but they cannot be set with MDItemSetAttribute() so
this script uses AppleScript to get the Finder to set the comment.

It's a bit of a hack but it works and will have to suffice until I can find whatever
undocumented API Finder actually uses to set the comment.
"""

import os
import typing as t

import applescript

kMDItemFinderComment = "kMDItemFinderComment"

__all__ = ["set_finder_comment", "kMDItemFinderComment"]

# AppleScript for manipulating Finder comments
_scpt_set_finder_comment = applescript.AppleScript(
    """
            on run {path, fc}
	            set thePath to path
	            set theComment to fc
	            tell application "Finder" to set comment of (POSIX file thePath as alias) to theComment
            end run
            """
)

_scpt_clear_finder_comment = applescript.AppleScript(
    """
            on run {path}
	            set thePath to path
	            set theComment to missing value
	            tell application "Finder" to set comment of (POSIX file thePath as alias) to theComment
            end run
            """
)


def set_finder_comment(path: str, comment: t.Optional[str]):
    """set finder comment for object path (file or directory)
    path: path to file or directory in posix format
    comment: comment string or None to clear comment
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find {path}")

    if comment:
        _scpt_set_finder_comment.run(path, comment)
    else:
        _clear_finder_comment(path)


def _clear_finder_comment(path: str):
    """clear finder comment for object path (file or directory)
    path: path to file or directory in posix format
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find {path}")

    _scpt_clear_finder_comment.run(path)
