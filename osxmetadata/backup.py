import json
import logging
import os

""" Functions for writing and loading backup files """


def write_backup_file(backup_file, backup_data):
    """ Write backup_data to backup_file as JSON
        backup_data: dict where key is filename and value is dict of the attributes
        as returned by json.loads(OSXMetaData.to_json()) """

    with open(backup_file, mode="w") as fp:
        for record in backup_data.values():
            json_str = json.dumps(record)
            fp.write(json_str)
            fp.write("\n")


def load_backup_file(backup_file):
    """ Load attribute data from JSON in backup_file 
        Returns: backup_data dict """

    if not os.path.isfile(backup_file):
        raise FileNotFoundError(f"Could not find backup file: {backup_file}")

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

    return backup_data
