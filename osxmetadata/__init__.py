#!/usr/bin/env python

from plistlib import loads, dumps, FMT_BINARY
from pathlib import Path
import pprint
from xattr import xattr
import os
import os.path
import sys
import tempfile
import subprocess
import datetime
from . import _applescript

# this was inspired by osx-tags by "Ben S / scooby" and is published under
# the same MIT license. See: https://github.com/scooby/osx-tags

# TODO: What to do about colors
# TODO: Add ability to remove key instead of just clear contents
# TODO: check what happens if OSXMetaData.__init__ called with invalid file--should result in error but saw one case where it didn't


# what to import
__all__ = ["OSXMetaData"]

# color labels
_COLORNAMES = {
    "None": 0,
    "Gray": 1,
    "Green": 2,
    "Purple": 3,
    "Blue": 4,
    "Yellow": 5,
    "Red": 6,
    "Orange": 7,
}

_COLORIDS = {
    0: "None",
    1: "Gray",
    2: "Green",
    3: "Purple",
    4: "Blue",
    5: "Yellow",
    6: "Red",
    7: "Orange",
}

_VALID_COLORIDS = "01234567"
_MAX_FINDERCOMMENT = 750  # determined through trial & error with Finder
_MAX_WHEREFROM = (
    1024
)  # just picked something....todo: need to figure out what max length is

_TAGS = "com.apple.metadata:_kMDItemUserTags"
_FINDER_COMMENT = "com.apple.metadata:kMDItemFinderComment"
_WHERE_FROM = "com.apple.metadata:kMDItemWhereFroms"
_DOWNLOAD_DATE = "com.apple.metadata:kMDItemDownloadedDate"


class _NullsInString(Exception):
    """Nulls in string."""


def _onError(e):
    sys.stderr.write(str(e) + "\n")


class _Tags:
    def __init__(self, xa: xattr):
        self.__attrs = xa
        self.__load_tags()

    def __tag_split(self, tag):
        """
        Extracts the color information from a Finder tag.
        """
        parts = tag.rsplit("\n", 1)
        if len(parts) == 1:
            return parts[0], 0
        elif (
            len(parts[1]) != 1 or parts[1] not in _VALID_COLORIDS
        ):  # Not a color number
            return tag, 0
        else:
            return parts[0], int(parts[1])

    def __load_tags(self):
        self.__tags = {}
        try:
            self.__tagvalues = self.__attrs[_TAGS]
            # load the binary plist value
            self.__tagvalues = loads(self.__tagvalues)
            for x in self.__tagvalues:
                (tag, color) = self.__tag_split(x)
                self.__tags[tag] = color
                # self.__tags = [self.__tag_strip_color(x) for x in self.__tagvalues]
        except KeyError:
            self.__tags = None
        if self.__tags:
            self.__tag_set = set(self.__tags.keys())
        else:
            self.__tag_set = set([])

    def __iter__(self):
        self.__load_tags()
        self.__tag_list = list(self.__tag_set)
        self.__tag_count = len(self.__tag_list)
        self.__tag_counter = 0
        return self

    def __next__(self):
        if self.__tag_counter < self.__tag_count:
            tag = self.__tag_list[self.__tag_counter]
            self.__tag_counter += 1
            return tag
        else:
            raise StopIteration

    def __len__(self):
        self.__load_tags()
        return len(self.__tag_set)

    def __repr__(self):
        self.__load_tags()
        return repr(self.__tag_set)

    def __str__(self):
        self.__load_tags()
        return ", ".join(self.__tag_set)

    def add(self, tag):
        if not isinstance(tag, str):
            raise TypeError("Tags must be strings")
        self.__load_tags()
        tags = set(map(self.__tag_normalize, self.__tag_set))
        tags.add(self.__tag_normalize(tag))
        self.__write_tags(*tags)

    def update(self, *tags):
        if not all(isinstance(tag, str) for tag in tags):
            raise TypeError("Tags must be strings")
        self.__load_tags()
        old_tags = set(map(self.__tag_normalize, self.__tag_set))
        new_tags = old_tags.union(set(map(self.__tag_normalize, tags)))
        self.__write_tags(*new_tags)

    def clear(self):
        try:
            self.__attrs.remove(_TAGS)
        except (IOError, OSError):
            pass

    def remove(self, tag):
        self.__load_tags()
        if not isinstance(tag, str):
            raise TypeError("Tags must be strings")
        tags = set(map(self.__tag_normalize, self.__tag_set))
        tags.remove(self.__tag_normalize(tag))
        self.__write_tags(*tags)

    def discard(self, tag):
        self.__load_tags()
        if not isinstance(tag, str):
            raise TypeError("Tags must be strings")
        tags = set(map(self.__tag_normalize, self.__tag_set))
        tags.discard(self.__tag_normalize(tag))
        self.__write_tags(*tags)

    def __iadd__(self, tag):
        self.add(tag)
        return self

    def __write_tags(self, *tags):
        """
        Overwrites the existing tags with the iterable of tags provided.
        """
        if not all(isinstance(tag, str) for tag in tags):
            raise TypeError("Tags must be strings")
        tag_plist = dumps(list(map(self.__tag_normalize, tags)), fmt=FMT_BINARY)
        self.__attrs.set(_TAGS, tag_plist)

    def __tag_colored(self, tag, color):
        """
        Sets the color of a tag.

        Parameters:
        tag(str): a tag name
        color(int): an integer from 1 through 7

        Return:
        (str) the tag with encoded color.
        """
        return "{}\n{}".format(self.__tag_nocolor(tag), color)

    def __tag_normalize(self, tag):
        """
        Ensures a color is set if not none.
        :param tag: a possibly non-normal tag.
        :return: A colorized tag.
        """
        tag, color = self.__tag_split(tag)
        if tag.title() in _COLORNAMES:
            # ignore the color passed and set proper color name
            return self.__tag_colored(tag.title(), _COLORNAMES[tag.title()])
        else:
            return self.__tag_colored(tag, color)

    def __tag_nocolor(self, tag):
        """
        Removes the color information from a Finder tag.
        """
        return tag.rsplit("\n", 1)[0]


class OSXMetaData:
    def __init__(self, fname):

        self.__fname = Path(fname)
        if not os.path.exists(self.__fname):
            raise (ValueError("file does not exist: ", fname))

        try:
            self.__attrs = xattr(self.__fname)
        except (IOError, OSError) as e:
            quit(_onError(e))

        # setup applescript for writing finder comments
        self.__scpt_set_finder_comment = _applescript.AppleScript(
            """
            on run {fname, fc}
	            set theFile to fname
	            set theComment to fc
	            tell application "Finder" to set comment of (POSIX file theFile as alias) to theComment
            end run
            """
        )

        # self.__setfc_script_fh = tempfile.NamedTemporaryFile(suffix=".scpt",prefix="osxmd",mode="w",delete=False)
        # self.__setfc_script = self.__setfc_script_fh.name
        # fd = self.__setfc_script_fh.file
        # fd.write(_APPLESCRIPT_SET_FINDER_COMMENT)
        # fd.close()
        # print("applescript = %s" % self.__setfc_script)

        # initialize meta data
        self.__tags = {}
        self.__findercomment = None
        self.__wherefrom = []
        self.__downloaddate = None

        self.tags = _Tags(self.__attrs)

        # TODO: Lot's of repetitive code here
        # need to read these dynamically
        """ Get Finder comment """
        self.__load_findercomment()

        """ Get Where From (for downloaded files) """
        self.__load_download_wherefrom()

        """ Get Download Date (for downloaded files) """
        self.__load_download_date()

    # @property
    # def colors(self):
    #     """ return list of color labels from tags
    #         do not return None (e.g. ignore tags with no color)
    #     """
    #     colors = []
    #     if self.__tags:
    #         for t in self.__tags.keys():
    #             c = self.__tags[t]
    #             if c == 0: continue
    #             colors.append(_COLORIDS[c])
    #         return colors
    #     else:
    #         return None

    def __del__(self):
        pass
        # print("removing temp file: %s" % self.__setfc_script)
        # os.remove(self.__setfc_script)

    def __load_findercomment(self):
        try:
            self.__fcvalue = self.__attrs[_FINDER_COMMENT]
            # load the binary plist value
            self.__findercomment = loads(self.__fcvalue)
        except KeyError:
            self.__findercomment = None

    @property
    def finder_comment(self):
        self.__load_findercomment()
        return self.__findercomment

    @finder_comment.setter
    def finder_comment(self, fc):
        """
        TODO: this creates a temporary script file which gets runs by osascript every time
              not very efficient.  Perhaps use py-applescript in the future but that increases
              dependencies + PyObjC
        """
        if fc is None:
            fc = ""
        elif not isinstance(fc, str):
            raise TypeError("Finder comment must be strings")

        if len(fc) > _MAX_FINDERCOMMENT:
            raise ValueError(
                "Finder comment limited to %d characters" % _MAX_FINDERCOMMENT
            )

        fname = self.__fname.resolve().as_posix()

        self.__scpt_set_finder_comment.run(fname, fc)

        self.__load_findercomment()

    def __load_download_wherefrom(self):
        try:
            self.__wfvalue = self.__attrs[_WHERE_FROM]
            # load the binary plist value
            self.__wherefrom = loads(self.__wfvalue)
        except KeyError:
            self.__wherefrom = None

    @property
    def where_from(self):
        self.__load_download_wherefrom()
        return self.__wherefrom

    @where_from.setter
    def where_from(self, wf):
        if wf is None:
            wf = []
        elif not isinstance(wf, list):
            raise TypeError("Where from must be a list of one or more URL strings")

        for w in wf:
            if len(w) > _MAX_WHEREFROM:
                raise ValueError(
                    "Where from URL limited to %d characters" % _MAX_WHEREFROM
                )

        wf_plist = dumps(wf, fmt=FMT_BINARY)
        self.__attrs.set(_WHERE_FROM, wf_plist)
        self.__load_download_wherefrom()

    def __load_download_date(self):
        try:
            self.__ddvalue = self.__attrs[_DOWNLOAD_DATE]
            # load the binary plist value
            # returns an array with a single datetime.datetime object
            self.__downloaddate = loads(self.__ddvalue)[0]
        except KeyError:
            self.__downloaddate = None

    @property
    def download_date(self):
        self.__load_download_date()
        return self.__downloaddate

    @download_date.setter
    def download_date(self, dt):
        if dt is None:
            dt = []
        elif not isinstance(dt, datetime.datetime):
            raise TypeError("Download date must be a datetime object")

        dt_plist = dumps([dt], fmt=FMT_BINARY)
        self.__attrs.set(_DOWNLOAD_DATE, dt_plist)
        self.__load_download_date()

    @property
    def name(self):
        return self.__fname.resolve().as_posix()
