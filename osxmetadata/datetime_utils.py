
""" datetime.datetime helper functions for converting to/from UTC """

import datetime

def get_local_tz(dt):
    """ return local timezone as datetime.timezone tzinfo for dt
    
    Args:
        dt: datetime.datetime
    
    Returns:
        local timezone for dt as datetime.timezone

    Raises:
        ValueError if dt is not timezone naive
    """
    if not datetime_has_tz(dt):
        return dt.astimezone().tzinfo
    else:
        raise ValueError("dt must be naive datetime.datetime object")


def datetime_has_tz(dt):
    """ return True if datetime dt has tzinfo else False
        dt: datetime.datetime
        returns True if dt is timezone aware, else False """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def datetime_tz_to_utc(dt):
    """ convert datetime.datetime object with timezone to UTC timezone 
        dt: datetime.datetime object
        returns: datetime.datetime in UTC timezone """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        return dt.replace(tzinfo=dt.tzinfo).astimezone(tz=datetime.timezone.utc)
    else:
        raise ValueError(f"dt does not have timezone info")


def datetime_remove_tz(dt):
    """ remove timezone from a datetime.datetime object
        dt: datetime.datetime object with tzinfo
        returns: dt without any timezone info (naive datetime object) """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    return dt.replace(tzinfo=None)


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

    return dt.replace(tzinfo=datetime.timezone.utc)


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

    return dt.replace(tzinfo=get_local_tz(dt))


def datetime_utc_to_local(dt):
    """ convert datetime.datetime object in UTC timezone to local timezone 
        dt: datetime.datetime object
        returns: datetime.datetime in local timezone """

    if type(dt) != datetime.datetime:
        raise TypeError(f"dt must be type datetime.datetime, not {type(dt)}")

    if dt.tzinfo is not datetime.timezone.utc:
        raise ValueError(f"{dt} must be in UTC timezone: timezone = {dt.tzinfo}")

    return dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
