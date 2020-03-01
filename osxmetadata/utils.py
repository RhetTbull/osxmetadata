import datetime
import json
import logging
import os

from . import _applescript
from .attributes import ATTRIBUTES

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


def load_backup_file(backup_file):
    """ Load attribute data from JSON in backup_file 
        Returns: backup_data dict """

    if not os.path.isfile(backup_file):
        raise FileNotFoundError(f"Could not find backup file: {backup_file}")

    backup_data = {}
    fp = open(backup_file, mode="r")

    for line in fp:
        data = json.loads(line)
        fname = data["_filename"]
        if fname in backup_data:
            logging.warning(
                f"WARNING: duplicate filename {fname} found in {backup_file}"
            )

        backup_data[fname] = data

    fp.close()
    return backup_data


def write_backup_file(backup_file, backup_data):
    """ Write backup_data to backup_file as JSON
        backup_data: dict where key is filename and value is dict of the attributes
        as returned by json.loads(OSXMetaData.to_json()) """

    fp = open(backup_file, mode="w")

    for record in backup_data.values():
        json_str = json.dumps(record)
        fp.write(json_str)
        fp.write("\n")

    fp.close()

