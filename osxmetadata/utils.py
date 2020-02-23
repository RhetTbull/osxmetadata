import datetime
import logging
import os

from . import _applescript

_DEBUG = False

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s",
)

if not _DEBUG:
    logging.disable(logging.DEBUG)


def _get_logger():
    """Used only for testing
    
    Returns:
        logging.Logger object -- logging.Logger object for osxmetadata
    """
    return logging.Logger(__name__)


def _set_debug(debug):
    """ Enable or disable debug logging """
    global _DEBUG
    _DEBUG = debug
    if debug:
        logging.disable(logging.NOTSET)
    else:
        logging.disable(logging.DEBUG)


def _debug():
    """ returns True if debugging turned on (via _set_debug), otherwise, false """
    return _DEBUG


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


def validate_attribute_value(attribute, value):
    """ validate that value is compatible with attribute.type_ 
        and convert value to correct type
        returns value as type attribute.type_ 
        value may be a single value or a list depending on what attribute expects 
        if value contains None, returns None """

    logging.debug(
        f"validate_attribute_value: attribute: {attribute}, value: {value}, type: {type(value)}"
    )

    # check to see if we got None
    try:
        if None in value:
            return None
    except TypeError:
        if value is None:
            return None

    try:
        if isinstance(value, str):
            value = [value]
        else:
            iter(value)
    except TypeError:
        # ZZZ handle passing in values as _AttributeSet, et
        # ZZZ also handle string which can iterate but we don't want it to
        value = [value]

    # # check for None and convert to list if needed
    # if not isinstance(value, list):
    #     if value is None:
    #         return None
    #     value = [value]
    # elif None in value:
    #     return None

    if not attribute.list and len(value) > 1:
        # got a list but didn't expect one
        raise ValueError(
            f"{attribute.name} expects only one value but list of {len(value)} provided"
        )

    new_values = []
    for val in value:
        new_val = None
        if attribute.type_ == str:
            new_val = str(val)
        elif attribute.type_ == float:
            try:
                new_val = float(val)
            except:
                raise TypeError(
                    f"{val} cannot be converted to expected type {attribute.type_}"
                )
        elif attribute.type_ == datetime.datetime:
            if not isinstance(val, datetime.datetime):
                # if not already a datetime.datetime, try to convert it
                try:
                    new_val = datetime.datetime.fromisoformat(val)
                except:
                    raise TypeError(
                        f"{val} cannot be converted to expected type {attribute.type_}"
                    )
            else:
                new_val = val
        else:
            raise TypeError(f"Unknown type: {type(val)}")
        new_values.append(new_val)

    logging.debug(f"new_value = {new_values}")
    if attribute.list:
        return new_values
    else:
        return new_values[0]
