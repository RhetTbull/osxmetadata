#!/usr/bin/env python

import datetime
import os
import os.path
import pathlib
import plistlib
import pprint
import subprocess
import sys
import tempfile

from plistlib import FMT_BINARY

from xattr import xattr

from . import _applescript


# this was inspired by osx-tags by "Ben S / scooby" and is published under
# the same MIT license. See: https://github.com/scooby/osx-tags

# TODO: What to do about colors
# TODO: Add ability to remove key instead of just clear contents
# TODO: check what happens if OSXMetaData.__init__ called with invalid file--should result in error but saw one case where it didn't
# TODO: cleartags does not always clear colors--this is a new behavior, did Mac OS change something in implementation of colors?

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
        self._attrs = xa
        self._load_tags()

    def _tag_split(self, tag):
        # Extracts the color information from a Finder tag.

        parts = tag.rsplit("\n", 1)
        if len(parts) == 1:
            return parts[0], 0
        elif (
            len(parts[1]) != 1 or parts[1] not in _VALID_COLORIDS
        ):  # Not a color number
            return tag, 0
        else:
            return parts[0], int(parts[1])

    def _load_tags(self):
        self._tags = {}
        try:
            self.__tagvalues = self._attrs[_TAGS]
            # load the binary plist value
            self.__tagvalues = plistlib.loads(self.__tagvalues)
            for x in self.__tagvalues:
                (tag, color) = self._tag_split(x)
                self._tags[tag] = color
                # self._tags = [self.__tag_strip_color(x) for x in self.__tagvalues]
        except KeyError:
            self._tags = None
        if self._tags:
            self.__tag_set = set(self._tags.keys())
        else:
            self.__tag_set = set([])

    def __iter__(self):
        self._load_tags()
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
        self._load_tags()
        return len(self.__tag_set)

    def __repr__(self):
        self._load_tags()
        return repr(self.__tag_set)

    def __str__(self):
        self._load_tags()
        return ", ".join(self.__tag_set)

    def add(self, tag):
        if not isinstance(tag, str):
            raise TypeError("Tags must be strings")
        self._load_tags()
        tags = set(map(self._tag_normalize, self.__tag_set))
        tags.add(self._tag_normalize(tag))
        self._write_tags(*tags)

    def update(self, *tags):
        if not all(isinstance(tag, str) for tag in tags):
            raise TypeError("Tags must be strings")
        self._load_tags()
        old_tags = set(map(self._tag_normalize, self.__tag_set))
        new_tags = old_tags.union(set(map(self._tag_normalize, tags)))
        self._write_tags(*new_tags)

    def clear(self):
        try:
            self._attrs.remove(_TAGS)
        except (IOError, OSError):
            pass

    def remove(self, tag):
        self._load_tags()
        if not isinstance(tag, str):
            raise TypeError("Tags must be strings")
        tags = set(map(self._tag_normalize, self.__tag_set))
        tags.remove(self._tag_normalize(tag))
        self._write_tags(*tags)

    def discard(self, tag):
        self._load_tags()
        if not isinstance(tag, str):
            raise TypeError("Tags must be strings")
        tags = set(map(self._tag_normalize, self.__tag_set))
        tags.discard(self._tag_normalize(tag))
        self._write_tags(*tags)

    def __iadd__(self, tag):
        self.add(tag)
        return self

    def _write_tags(self, *tags):
        # Overwrites the existing tags with the iterable of tags provided.

        if not all(isinstance(tag, str) for tag in tags):
            raise TypeError("Tags must be strings")
        tag_plist = plistlib.dumps(list(map(self._tag_normalize, tags)), fmt=FMT_BINARY)
        self._attrs.set(_TAGS, tag_plist)

    def _tag_colored(self, tag, color):
        """
        Sets the color of a tag.

        Parameters:
        tag(str): a tag name
        color(int): an integer from 1 through 7

        Return:
        (str) the tag with encoded color.
        """
        return "{}\n{}".format(self._tag_nocolor(tag), color)

    def _tag_normalize(self, tag):
        """
        Ensures a color is set if not none.
        :param tag: a possibly non-normal tag.
        :return: A colorized tag.
        """
        tag, color = self._tag_split(tag)
        if tag.title() in _COLORNAMES:
            # ignore the color passed and set proper color name
            return self._tag_colored(tag.title(), _COLORNAMES[tag.title()])
        else:
            return self._tag_colored(tag, color)

    def _tag_nocolor(self, tag):
        """
        Removes the color information from a Finder tag.
        """
        return tag.rsplit("\n", 1)[0]


class OSXMetaData:
    """Create an OSXMetaData object to access file metadata"""

    def __init__(self, fname):
        """Create an OSXMetaData object to access file metadata"""
        self.__fname = pathlib.Path(fname)
        if not self.__fname.exists():
            raise ValueError("file does not exist: ", fname)

        try:
            self._attrs = xattr(self.__fname)
        except (IOError, OSError) as e:
            quit(_onError(e))

        # setup applescript for writing finder comments
        self._scpt_set_finder_comment = _applescript.AppleScript(
            """
            on run {fname, fc}
	            set theFile to fname
	            set theComment to fc
	            tell application "Finder" to set comment of (POSIX file theFile as alias) to theComment
            end run
            """
        )

        # initialize meta data
        self._tags = {}
        self._findercomment = None
        self._wherefrom = []
        self._downloaddate = None

        self.tags = _Tags(self._attrs)

        # TODO: Lot's of repetitive code here
        # need to read these dynamically
        self._load_findercomment()

        self._load_download_wherefrom()

        self._load_download_date()

    # @property
    # def colors(self):
    #     """ return list of color labels from tags
    #         do not return None (e.g. ignore tags with no color)
    #     """
    #     colors = []
    #     if self._tags:
    #         for t in self._tags.keys():
    #             c = self._tags[t]
    #             if c == 0: continue
    #             colors.append(_COLORIDS[c])
    #         return colors
    #     else:
    #         return None

    def __del__(self):
        pass
        # print("removing temp file: %s" % self.__setfc_script)
        # os.remove(self.__setfc_script)

    def _load_findercomment(self):
        try:
            self.__fcvalue = self._attrs[_FINDER_COMMENT]
            # load the binary plist value
            self._findercomment = plistlib.loads(self.__fcvalue)
        except KeyError:
            self._findercomment = None

    @property
    def finder_comment(self):
        """ Get/set the Finder comment (or None) associated with the file.
            Functions as a string: e.g. finder_comment += 'my comment'. """
        self._load_findercomment()
        return self._findercomment

    @finder_comment.setter
    def finder_comment(self, fc):
        # TODO: this creates a temporary script file which gets runs by osascript every time
        #       not very efficient.  Perhaps use py-applescript in the future but that increases
        #       dependencies + PyObjC

        if fc is None:
            fc = ""
        elif not isinstance(fc, str):
            raise TypeError("Finder comment must be strings")

        if len(fc) > _MAX_FINDERCOMMENT:
            raise ValueError(
                "Finder comment limited to %d characters" % _MAX_FINDERCOMMENT
            )

        fname = self.__fname.resolve().as_posix()

        self._scpt_set_finder_comment.run(fname, fc)

        self._load_findercomment()

    def _load_download_wherefrom(self):
        try:
            self.__wfvalue = self._attrs[_WHERE_FROM]
            # load the binary plist value
            self._wherefrom = plistlib.loads(self.__wfvalue)
        except KeyError:
            self._wherefrom = None

    @property
    def where_from(self):
        """ Get/set list of URL(s) where file was downloaded from. """
        self._load_download_wherefrom()
        return self._wherefrom

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

        wf_plist = plistlib.dumps(wf, fmt=FMT_BINARY)
        self._attrs.set(_WHERE_FROM, wf_plist)
        self._load_download_wherefrom()

    def _load_download_date(self):
        try:
            # logger.debug(self.__fname)
            self.__ddvalue = self._attrs[_DOWNLOAD_DATE]
            # logger.debug(self.__ddvalue)
            # load the binary plist value
            # returns an array with a single datetime.datetime object
            self._downloaddate = plistlib.loads(self.__ddvalue)[0]
            # logger.debug(self._downloaddate)
        except KeyError:
            self._downloaddate = None
        except:
            pass
            # logger.debug("Not a KeyError")
            # TODO: is this needed?

    @property
    def download_date(self):
        """ Get/set date file was downloaded, as a datetime.datetime object. """
        self._load_download_date()
        return self._downloaddate

    @download_date.setter
    def download_date(self, dt):
        if dt is None:
            dt = []
        elif not isinstance(dt, datetime.datetime):
            raise TypeError("Download date must be a datetime object")

        dt_plist = plistlib.dumps([dt], fmt=FMT_BINARY)
        self._attrs.set(_DOWNLOAD_DATE, dt_plist)
        self._load_download_date()

    @property
    def name(self):
        """ The file name """
        return self.__fname.resolve().as_posix()
