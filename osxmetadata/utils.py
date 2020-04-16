import datetime
import json
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


# datetime.datetime helper functions for converting to/from UTC


def get_local_tz():
    """ return local timezone as datetime.timezone tzinfo """
    local_tz = (
        datetime.datetime.now(datetime.timezone(datetime.timedelta(0)))
        .astimezone()
        .tzinfo
    )
    return local_tz


def datetime_has_tz(dt):
    """ return True if datetime dt has tzinfo else False
        dt: datetime.datetime
        returns True if dt is timezone aware, else False """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        return True
    return False


def datetime_tz_to_utc(dt):
    """ convert datetime.datetime object with timezone to UTC timezone 
        dt: datetime.datetime object
        returns: datetime.datetime in UTC timezone """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    local_tz = get_local_tz()
    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        dt_utc = dt.replace(tzinfo=dt.tzinfo).astimezone(tz=datetime.timezone.utc)
        return dt_utc
    else:
        raise ValueError(f"dt does not have timezone info")


def datetime_remove_tz(dt):
    """ remove timezone from a datetime.datetime object
        dt: datetime.datetime object with tzinfo
        returns: dt without any timezone info (naive datetime object) """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    dt_new = dt.replace(tzinfo=None)
    return dt_new


def datetime_naive_to_utc(dt):
    """ convert naive (timezone unaware) datetime.datetime
        to aware timezone in UTC timezone
        dt: datetime.datetime without timezone
        returns: datetime.datetime with UTC timezone """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        # has timezone info
        raise ValueError(
            "dt must be naive/timezone unaware: "
            f"{dt} has tzinfo {dt.tzinfo} and offset {dt.tzinfo.utcoffset(dt)}"
        )

    dt_utc = dt.replace(tzinfo=datetime.timezone.utc)
    return dt_utc


def datetime_naive_to_local(dt):
    """ convert naive (timezone unaware) datetime.datetime
        to aware timezone in local timezone
        dt: datetime.datetime without timezone
        returns: datetime.datetime with local timezone """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        # has timezone info
        raise ValueError(
            "dt must be naive/timezone unaware: "
            f"{dt} has tzinfo {dt.tzinfo} and offset {dt.tizinfo.utcoffset(dt)}"
        )

    dt_local = dt.replace(tzinfo=get_local_tz())
    return dt_local


def datetime_utc_to_local(dt):
    """ convert datetime.datetime object in UTC timezone to local timezone 
        dt: datetime.datetime object
        returns: datetime.datetime in local timezone """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    if dt.tzinfo is not datetime.timezone.utc:
        raise ValueError(f"{dt} must be in UTC timezone: timezone = {dt.tzinfo}")

    dt_local = dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=get_local_tz())
    return dt_local
