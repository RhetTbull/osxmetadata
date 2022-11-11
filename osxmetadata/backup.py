""" Functions for writing and loading backup files """

import datetime
import json
import logging
import os
from enum import Enum

from osxmetadata import OSXMetaData, __version__

__all__ = ["get_backup_dict", "write_backup_file", "load_backup_file"]


class BackupDatabaseType(Enum):
    SINGLE_RECORD_JSON = 1
    JSON = 2


def get_backup_dict(filepath: str):
    """get backup dict for a single file"""
    md = OSXMetaData(filepath)
    try:
        backup_dict = md.asdict()
    except Exception as e:
        logging.warning(f"Error retrieving metadata for file {filepath}: {e}")
        backup_dict = {}

    backup_dict.update(
        {
            "_version": __version__,
            "_filename": md._fname.name,
            "_filepath": md._posix_path,
        }
    )
    return backup_dict


def backup_database_type(path: str) -> BackupDatabaseType:
    """Return BackupDatabaseType enum indicating type of backup file for path"""
    with open(path) as fp:
        line = fp.readline()
        if not line:
            raise ValueError("Unknown backup file type")
        ch = line[0]
        if ch == "{":
            return BackupDatabaseType.SINGLE_RECORD_JSON
        elif ch == "[":
            return BackupDatabaseType.JSON
        else:
            raise ValueError("Unknown backup file type")


def write_backup_file(backup_file, backup_data):
    """Write backup_data to backup_file as JSON
    backup_data: dict where key is filename and value is dict of the attributes
    as returned by json.loads(OSXMetaData.to_json())"""

    # Convert datetime objects to isoformat strings for serialization
    for filename, data in backup_data.items():
        for key, value in data.items():
            if isinstance(value, datetime.datetime):
                data[key] = value.isoformat()
            elif isinstance(value, (list, tuple)):
                if value and isinstance(value[0], datetime.datetime):
                    data[key] = [v.isoformat() for v in value]
        # strip null values
        data = {k: v for k, v in data.items() if v is not None}
        backup_data[filename] = data

    with open(backup_file, mode="w") as fp:
        json.dump(list(backup_data.values()), fp, indent=2)


def load_backup_file(backup_file):
    """Load attribute data from JSON in backup_file
    Returns: backup_data dict"""

    if not os.path.isfile(backup_file):
        raise FileNotFoundError(f"Could not find backup file: {backup_file}")

    if backup_database_type(backup_file) == BackupDatabaseType.SINGLE_RECORD_JSON:
        # old style single record of json per file
        backup_data = {}
        with open(backup_file, mode="r") as fp:
            for line in fp:
                data = json.loads(line)
                fname = data["_filename"]
                if fname in backup_data:
                    logging.warning(
                        f"WARNING: duplicate filename {fname} found in {backup_file}"
                    )

                backup_data[fname] = data
    else:
        with open(backup_file, mode="r") as fp:
            backup_records = json.load(fp)
        backup_data = {data["_filename"]: data for data in backup_records}

    return backup_data
