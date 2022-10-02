""" Constants and validation for metadata attributes that can be set """


import datetime
from collections import namedtuple  # pylint: disable=syntax-error

from .classes import (
    _AttributeFinderInfo,
    _AttributeFinderInfoColor,
    _AttributeFinderInfoStationeryPad,
    _AttributeList,
    _AttributeTagsList,
    _AttributeOSXPhotosDetectedText,
)
from .constants import *
from .datetime_utils import (
    datetime_has_tz,
    datetime_naive_to_local,
    datetime_remove_tz,
    datetime_tz_to_utc,
)

# used for formatting output of --list
# _SHORT_NAME_WIDTH = max(len(x) for x in ATTRIBUTES) + 5
# _LONG_NAME_WIDTH = max(len(x.constant) for x in ATTRIBUTES.values()) + 10
# _CONSTANT_WIDTH = 21 + 5  # currently longest is kMDItemDownloadedDate


def validate_attribute_value(attribute, value):
    """validate that value is compatible with attribute.type_
    and convert value to correct type
    returns value as type attribute.type_
    value may be a single value or a list depending on what attribute expects
    if value contains None, returns None
    """

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

    if not attribute.list and len(value) > 1:
        # got a list but didn't expect one
        raise ValueError(
            f"{attribute.name} expects only one value but list of {len(value)} provided"
        )

    if attribute.class_ == _AttributeOSXPhotosDetectedText:
        return _AttributeOSXPhotosDetectedText.validate_value(value)

    new_values = []
    for val in value:
        new_val = None
        if attribute.type_ == str:
            new_val = str(val)
        elif attribute.type_ == float:
            try:
                new_val = float(val)
            except ValueError:
                # todo: should this really raise ValueError?
                raise TypeError(
                    f"{val} cannot be converted to expected type {attribute.type_}"
                )
        elif attribute.type_ == int:
            try:
                new_val = int(val)
            except ValueError:
                raise TypeError(
                    f"{val} cannot be converted to expected type {attribute.type_}"
                )
        elif attribute.type_ == bool:
            try:
                new_val = bool(val)
            except ValueError:
                raise TypeError(
                    f"{val} cannot be converted to expected type {attribute.type_}"
                )
        elif attribute.type_ == datetime.datetime:
            if isinstance(val, datetime.datetime):
                new_val = val
            elif not val:
                new_val = None
            else:
                try:
                    new_val = datetime.datetime.fromisoformat(val)
                except ValueError:
                    raise TypeError(
                        f"{val} cannot be converted to expected type {attribute.type_}"
                    )
            if isinstance(new_val, datetime.datetime):
                if not datetime_has_tz(new_val):
                    # assume it's in local time, so add local timezone,
                    # convert to UTC, then drop timezone
                    new_val = datetime_naive_to_local(new_val)
                # convert to UTC and remove timezone
                new_val = datetime_tz_to_utc(new_val)
                new_val = datetime_remove_tz(new_val)
        elif attribute.type_ == list:
            new_val = val if isinstance(val, (list, tuple)) else [val]
        else:
            raise TypeError(f"Unknown type: {type(val)}")
        new_values.append(new_val)

    if attribute.list:
        return new_values
    else:
        return new_values[0]
