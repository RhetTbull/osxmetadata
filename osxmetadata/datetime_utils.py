
""" datetime.datetime helper functions for converting to/from UTC """

import datetime

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
