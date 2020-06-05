""" Manipulating Finder comments """

import os.path

from . import _applescript

_scpt_set_finder_comment = _applescript.AppleScript(
    """
            on run {path, fc}
	            set thePath to path
	            set theComment to fc
	            tell application "Finder" to set comment of (POSIX file thePath as alias) to theComment
            end run
            """
)

_scpt_clear_finder_comment = _applescript.AppleScript(
    """
            on run {path}
	            set thePath to path
	            set theComment to missing value
	            tell application "Finder" to set comment of (POSIX file thePath as alias) to theComment
            end run
            """
)


def set_finder_comment(path, comment):
    """ set finder comment for object path (file or directory)
        path: path to file or directory in posix format
        comment: comment string
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find {path}")

    _scpt_set_finder_comment.run(path, comment)


def clear_finder_comment(path):
    """ clear finder comment for object path (file or directory)
        path: path to file or directory in posix format
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find {path}")

    _scpt_clear_finder_comment.run(path)
