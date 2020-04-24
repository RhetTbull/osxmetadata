""" Manipulating Finder comments """

import os.path

from . import _applescript

_scpt_set_finder_comment = _applescript.AppleScript(
    """
            on run {fname, fc}
	            set theFile to fname
	            set theComment to fc
	            tell application "Finder" to set comment of (POSIX file theFile as alias) to theComment
            end run
            """
)

_scpt_clear_finder_comment = _applescript.AppleScript(
    """
            on run {fname}
	            set theFile to fname
	            set theComment to missing value
	            tell application "Finder" to set comment of (POSIX file theFile as alias) to theComment
            end run
            """
)


def set_finder_comment(filename, comment):
    """ set finder comment for filename
        filename: path to file in posix format
        comment: comment string
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Could not find {filename}")

    _scpt_set_finder_comment.run(filename, comment)


def clear_finder_comment(filename):
    """ clear finder comment for filename
        filename: path to file in posix format
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Could not find {filename}")

    _scpt_clear_finder_comment.run(filename)
