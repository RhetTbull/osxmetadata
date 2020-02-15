""" Python module to read and write various Mac OS X metadata 
    such as tags/keywords and Finder comments from files """

import datetime
import os
import os.path
import pathlib
import plistlib
import pprint
import subprocess
import sys
import tempfile

# plistlib creates constants at runtime which causes pylint to complain
from plistlib import FMT_BINARY  # pylint: disable=E0611

import xattr

from . import _applescript
from ._constants import (
    _COLORIDS,
    _COLORNAMES,
    _DOWNLOAD_DATE,
    _FINDER_COMMENT,
    _MAX_FINDERCOMMENT,
    _MAX_WHEREFROM,
    _TAGS,
    _VALID_COLORIDS,
    _WHERE_FROM,
    _ATTRIBUTES,
)

# this was inspired by osx-tags by "Ben S / scooby" and is published under
# the same MIT license. See: https://github.com/scooby/osx-tags

# TODO: What to do about colors
# TODO: Add ability to remove key instead of just clear contents
# TODO: check what happens if OSXMetaData.__init__ called with invalid file--should result in error but saw one case where it didn't
# TODO: cleartags does not always clear colors--this is a new behavior, did Mac OS change something in implementation of colors?

# what to import
__all__ = ["OSXMetaData"]


class _NullsInString(Exception):
    """Nulls in string."""


def _onError(e):
    sys.stderr.write(str(e) + "\n")


class _Tags:
    """ represents a tag/keyword """

    def __init__(self, xa: xattr.xattr):
        self._attrs = xa

        # used for __iter__
        self._tag_list = None
        self._tag_count = None
        self._tag_counter = None

        # initialize
        self._load_tags()

    def add(self, tag):
        """ add a tag """
        if not isinstance(tag, str):
            raise TypeError("Tags must be strings")
        self._load_tags()
        tags = set(map(self._tag_normalize, self._tag_set))
        tags.add(self._tag_normalize(tag))
        self._write_tags(*tags)

    def update(self, *tags):
        """ update tag list adding any new tags in *tags """
        if not all(isinstance(tag, str) for tag in tags):
            raise TypeError("Tags must be strings")
        self._load_tags()
        old_tags = set(map(self._tag_normalize, self._tag_set))
        new_tags = old_tags.union(set(map(self._tag_normalize, tags)))
        self._write_tags(*new_tags)

    def clear(self):
        """ clear tags (remove all tags) """
        try:
            self._attrs.remove(_TAGS)
        except (IOError, OSError):
            pass

    def remove(self, tag):
        """ remove a tag, raise exception if tag does not exist """
        self._load_tags()
        if not isinstance(tag, str):
            raise TypeError("Tags must be strings")
        tags = set(map(self._tag_normalize, self._tag_set))
        tags.remove(self._tag_normalize(tag))
        self._write_tags(*tags)

    def discard(self, tag):
        """ remove a tag, does not raise exception if tag does not exist """
        self._load_tags()
        if not isinstance(tag, str):
            raise TypeError("Tags must be strings")
        tags = set(map(self._tag_normalize, self._tag_set))
        tags.discard(self._tag_normalize(tag))
        self._write_tags(*tags)

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
            self._tagvalues = self._attrs[_TAGS]
            # load the binary plist value
            self._tagvalues = plistlib.loads(self._tagvalues)
            for x in self._tagvalues:
                (tag, color) = self._tag_split(x)
                self._tags[tag] = color
                # self._tags = [self._tag_strip_color(x) for x in self._tagvalues]
        except KeyError:
            self._tags = None
        if self._tags:
            self._tag_set = set(self._tags.keys())
        else:
            self._tag_set = set([])

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

    def __iter__(self):
        self._load_tags()
        self._tag_list = list(self._tag_set)
        self._tag_count = len(self._tag_list)
        self._tag_counter = 0
        return self

    def __next__(self):
        if self._tag_counter < self._tag_count:
            tag = self._tag_list[self._tag_counter]
            self._tag_counter += 1
            return tag
        else:
            raise StopIteration

    def __len__(self):
        self._load_tags()
        return len(self._tag_set)

    def __repr__(self):
        self._load_tags()
        return repr(self._tag_set)

    def __str__(self):
        self._load_tags()
        return ", ".join(self._tag_set)

    def __iadd__(self, tag):
        self.add(tag)
        return self


class OSXMetaData:
    """Create an OSXMetaData object to access file metadata"""

    def __init__(self, fname):
        """Create an OSXMetaData object to access file metadata"""
        self._fname = pathlib.Path(fname)
        if not self._fname.exists():
            raise ValueError("file does not exist: ", fname)

        try:
            self._attrs = xattr.xattr(self._fname)
        except (IOError, OSError) as e:
            quit(_onError(e))

        self._data = {}

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

        self.tags = _Tags(self._attrs)

        # TODO: Lot's of repetitive code here
        # need to read these dynamically
        self._load_findercomment()
        self._load_download_wherefrom()
        self._load_download_date()

    @property
    def finder_comment(self):
        """ Get/set the Finder comment (or None) associated with the file.
            Functions as a string: e.g. finder_comment += 'my comment'. """
        self._load_findercomment()
        return self._data[_FINDER_COMMENT]

    @finder_comment.setter
    def finder_comment(self, fc):
        """ Get/set the Finder comment (or None) associated with the file.
            Functions as a string: e.g. finder_comment += 'my comment'. """
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

        fname = self._fname.resolve().as_posix()
        self._scpt_set_finder_comment.run(fname, fc)
        self._load_findercomment()

    @property
    def where_from(self):
        """ Get/set list of URL(s) where file was downloaded from. """
        self._load_download_wherefrom()
        return self._data[_WHERE_FROM]

    @where_from.setter
    def where_from(self, wf):
        """ Get/set list of URL(s) where file was downloaded from. """
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

    @property
    def download_date(self):
        """ Get/set date file was downloaded, as a datetime.datetime object. """
        self._load_download_date()
        return self._data[_DOWNLOAD_DATE]

    @download_date.setter
    def download_date(self, dt):
        """ Get/set date file was downloaded, as a datetime.datetime object. """
        if dt is None:
            dt = []
        elif not isinstance(dt, datetime.datetime):
            raise TypeError("Download date must be a datetime object")

        dt_plist = plistlib.dumps([dt], fmt=FMT_BINARY)
        self._attrs.set(_DOWNLOAD_DATE, dt_plist)
        self._load_download_date()

    @property
    def name(self):
        """ POSIX path of the file OSXMetaData is operating on """
        return self._fname.resolve().as_posix()

    ### Experimenting with generic method of reading / writing attributes
    def load_attribute(self, attribute):
        """ load attribute and return value or None if attribute was not set 
        """
        attr_name = _ATTRIBUTES[attribute].constant
        try:
            plist = plistlib.loads(self._attrs[attr_name])
        except KeyError:
            plist = None

        if _ATTRIBUTES[attribute].as_list and isinstance(plist, list):
            return plist[0]
        else:
            return plist

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

    def _load_findercomment(self):
        try:
            # load the binary plist value
            self._data[_FINDER_COMMENT] = plistlib.loads(self._attrs[_FINDER_COMMENT])
        except KeyError:
            self._data[_FINDER_COMMENT] = None

    def _load_download_wherefrom(self):
        try:
            # load the binary plist value
            self._data[_WHERE_FROM] = plistlib.loads(self._attrs[_WHERE_FROM])
        except KeyError:
            self._data[_WHERE_FROM] = None

    def _load_download_date(self):
        try:
            # load the binary plist value
            # returns an array with a single datetime.datetime object
            self._data[_DOWNLOAD_DATE] = plistlib.loads(self._attrs[_DOWNLOAD_DATE])[0]
            # logger.debug(self._downloaddate)
        except KeyError:
            self._data[_DOWNLOAD_DATE] = None
