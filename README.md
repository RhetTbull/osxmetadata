# osxmetadata 
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## What is osxmetadata?

osxmetadata provides a simple interface to access various metadata about MacOS / OS X files.  Currently supported metadata attributes include tags/keywords, Finder comments, authors, etc.  

## Motivation

Apple provides rich support for file metadata through various metadata extended attributes.  MacOS provides tools to view and set these various metadata attributes.  For example, `mdls` lists metadata associated with a file but doesn't let you edit the data while `xattr` allows the user to set extended attributes but requires the values be in the form of a MacOS plist which is impractical.   `osxmetadata` makes it easy to to both view and manipulate the MacOS metadata attributes, either programmatically or through a command line tool.

## Supported operating systems

Only works on MacOS.  Requires Python 3.7+. 

## Installation instructions

osxmetadata uses setuptools, thus simply run:

	python setup.py install

## Command Line Usage

Installs command line tool called osxmetadata which provides a simple interface to view/edit metadata supported by osxmetadata.

If you only care about the command line tool, I recommend installing with [pipx](https://github.com/pipxproject/pipx)

The command line tool can also be run via `python -m osxmetadata`.  Running it with no arguments or with --help option will print a help message:

```
Usage: osxmetadata [OPTIONS] FILE
  
  Read/write metadata from file(s).

Options:
  -v, --version                   Show the version and exit.
  -h, --help                      Show this message and exit.
  -w, --walk                      Walk directory tree, processing each file in
                                  the tree.
  -j, --json                      Print output in JSON format, for use with
                                  --list and --get.
  -X, --wipe                      Wipe all metadata attributes from FILE.
  -s, --set ATTRIBUTE VALUE       Set ATTRIBUTE to VALUE.
  -l, --list                      List all metadata attributes for FILE.
  -c, --clear ATTRIBUTE           Remove attribute from FILE.
  -a, --append ATTRIBUTE VALUE    Append VALUE to ATTRIBUTE.
  -g, --get ATTRIBUTE             Get value of ATTRIBUTE.
  -r, --remove ATTRIBUTE VALUE    Remove VALUE from ATTRIBUTE; only applies to
                                  multi-valued attributes.
  -u, --update ATTRIBUTE VALUE    Update ATTRIBUTE with VALUE; for multi-
                                  valued attributes, this adds VALUE to the
                                  attribute if not already in the list.
  -m, --mirror ATTRIBUTE1 ATTRIBUTE2
                                  Mirror values between ATTRIBUTE1 and
                                  ATTRIBUTE2 so that ATTRIBUTE1 = ATTRIBUTE2;
                                  for multi-valued attributes, merges values;
                                  for string attributes, sets ATTRIBUTE1 =
                                  ATTRIBUTE2 overwriting any value in
                                  ATTRIBUTE1.  For example: '--mirror keywords
                                  tags' sets tags and keywords to same values.
  -B, --backup                    Backup FILE attributes.  Backup file
                                  '.osxmetadata.json' will be created in same
                                  folder as FILE. Only backs up attributes
                                  known to osxmetadata unless used with --all.
  -R, --restore                   Restore FILE attributes from backup file.
                                  Restore will look for backup file
                                  '.osxmetadata.json' in same folder as FILE.
                                  Only restores attributes known to
                                  osxmetadata unless used with --all.
  -A, --all                       Process all extended attributes including
                                  those not known to osxmetadata. Use with
                                  --backup/--restore to backup/restore all
                                  extended attributes.
  -V, --verbose                   Print verbose output.
  -f, --copyfrom SOURCE_FILE      Copy attributes from file SOURCE_FILE.
  --files-only                    Do not apply metadata commands to
                                  directories themselves, only files in a
                                  directory.
  -p, --pattern PATTERN           Only process files matching PATTERN; only
                                  applies to --walk. If specified, only files
                                  matching PATTERN will be processed as each
                                  directory is walked. May be used for than
                                  once to specify multiple patterns. For
                                  example, tag all *.pdf files in projectdir
                                  and subfolders with tag 'project':
                                  osxmetadata --append tags 'project' --walk
                                  projectdir/ --pattern '*.pdf'

Valid attributes for ATTRIBUTE: Each attribute has a short name, a constant
name, and a long constant name. Any of these may be used for ATTRIBUTE

For example: --set findercomment "Hello world"
or:          --set kMDItemFinderComment "Hello world"
or:          --set com.apple.metadata:kMDItemFinderComment "Hello world"

Attributes that are strings can only take one value for --set; --append will
append to the existing value.  Attributes that are arrays can be set multiple
times to add to the array: e.g. --set keywords 'foo' --set keywords 'bar' will
set keywords to ['foo', 'bar']

Options are executed in the following order regardless of order passed on the
command line: restore, wipe, copyfrom, clear, set, append, update, remove,
mirror, get, list, backup.  --backup and --restore are mutually exclusive.
Other options may be combined or chained together.

Finder tags (tags attribute) contain both a name and an optional color. To
specify the color, append comma + color name (e.g. 'red') after the tag name.
For example --set tags Foo,red. Valid color names are: gray, green, purple,
blue, yellow, red, orange. If color is not specified but a tag of the same
name has already been assigned a color in the Finder, the same color will
automatically be assigned.

com.apple.FinderInfo (finderinfo) value is a key:value dictionary. To set
finderinfo, pass value in format key1:value1,key2:value2,etc. For example:
'osxmetadata --set finderinfo color:2 file.ext'.

Short Name      Description
authors         kMDItemAuthors, com.apple.metadata:kMDItemAuthors; The
                author, or authors, of the contents of the file.  A list of
                strings.
comment         kMDItemComment, com.apple.metadata:kMDItemComment; A comment
                related to the file.  This differs from the Finder comment,
                kMDItemFinderComment.  A string.
copyright       kMDItemCopyright, com.apple.metadata:kMDItemCopyright; The
                copyright owner of the file contents.  A string.
creator         kMDItemCreator, com.apple.metadata:kMDItemCreator;
                Application used to create the document content (for example
                “Word”, “Pages”, and so on).  A string.
description     kMDItemDescription, com.apple.metadata:kMDItemDescription; A
                description of the content of the resource.  The description
                may include an abstract, table of contents, reference to a
                graphical representation of content or a free-text account
                of the content.  A string.
downloadeddate  kMDItemDownloadedDate,
                com.apple.metadata:kMDItemDownloadedDate; The date the item
                was downloaded.  A date in ISO 8601 format, time and
                timezone offset are optional: e.g. 2020-04-14T12:00:00 (ISO
                8601 w/o timezone), 2020-04-14 (ISO 8601 w/o time and time
                zone), or 2020-04-14T12:00:00-07:00 (ISO 8601 with timezone
                offset). Times without timezone offset are assumed to be in
                local timezone.
duedate         kMDItemDueDate, com.apple.metadata:kMDItemDueDate; The date
                the item is due.  A date in ISO 8601 format, time and
                timezone offset are optional: e.g. 2020-04-14T12:00:00 (ISO
                8601 w/o timezone), 2020-04-14 (ISO 8601 w/o time and time
                zone), or 2020-04-14T12:00:00-07:00 (ISO 8601 with timezone
                offset). Times without timezone offset are assumed to be in
                local timezone.
findercolor     findercolor, com.apple.FinderInfo; Color tag set by the
                Finder.  Colors can also be set by _kMDItemUserTags.  This
                is controlled by the Finder and it's recommended you don't
                directly access this attribute.  If you set or remove a
                color tag via _kMDItemUserTag, osxmetadata will
                automatically handle processing of FinderInfo color tag.
findercomment   kMDItemFinderComment,
                com.apple.metadata:kMDItemFinderComment; Finder comments for
                this file.  A string.
finderinfo      finderinfo, com.apple.FinderInfo; Info set by the Finder,
                for example tag color.  Colors can also be set by
                _kMDItemUserTags.  com.apple.FinderInfo is controlled by the
                Finder and it's recommended you don't directly access this
                attribute.  If you set or remove a color tag via
                _kMDItemUserTag, osxmetadata will automatically handle
                processing of FinderInfo color tag.
headline        kMDItemHeadline, com.apple.metadata:kMDItemHeadline; A
                publishable entry providing a synopsis of the contents of
                the file.  A string.
keywords        kMDItemKeywords, com.apple.metadata:kMDItemKeywords;
                Keywords associated with this file. For example, “Birthday”,
                “Important”, etc. This differs from Finder tags
                (_kMDItemUserTags) which are keywords/tags shown in the
                Finder and searchable in Spotlight using "tag:tag_name".  A
                list of strings.
participants    kMDItemParticipants, com.apple.metadata:kMDItemParticipants;
                The list of people who are visible in an image or movie or
                written about in a document. A list of strings.
projects        kMDItemProjects, com.apple.metadata:kMDItemProjects; The
                list of projects that this file is part of. For example, if
                you were working on a movie all of the files could be marked
                as belonging to the project “My Movie”. A list of strings.
rating          kMDItemStarRating, com.apple.metadata:kMDItemStarRating;
                User rating of this item. For example, the stars rating of
                an iTunes track. An integer.
stationary      kMDItemFSIsStationery,
                com.apple.metadata:kMDItemFSIsStationery; Boolean indicating
                if this file is stationery.
tags            _kMDItemUserTags, com.apple.metadata:_kMDItemUserTags;
                Finder tags; searchable in Spotlight using "tag:tag_name".
                If you want tags/keywords visible in the Finder, use this
                instead of kMDItemKeywords.  A list of Tag objects.
version         kMDItemVersion, com.apple.metadata:kMDItemVersion; The
                version number of this file. A string.
wherefroms      kMDItemWhereFroms, com.apple.metadata:kMDItemWhereFroms;
                Describes where the file was obtained from (e.g. URL
                downloaded from).  A list of strings.
```


## Supported Attributes

Information about commonly used MacOS metadata attributes is available from [Apple](https://developer.apple.com/documentation/coreservices/file_metadata/mditem/common_metadata_attribute_keys?language=objc).  

`osxmetadata` currently supports the following metadata attributes:

| Constant | Short Name | Long Constant | Description |
|---------------|----------|---------|-----------|
|kMDItemAuthors|authors|com.apple.metadata:kMDItemAuthors|The author, or authors, of the contents of the file.  A list of strings.|
|kMDItemComment|comment|com.apple.metadata:kMDItemComment|A comment related to the file.  This differs from the Finder comment, kMDItemFinderComment.  A string.|
|kMDItemCopyright|copyright|com.apple.metadata:kMDItemCopyright|The copyright owner of the file contents.  A string.|
|kMDItemCreator|creator|com.apple.metadata:kMDItemCreator|Application used to create the document content (for example “Word”, “Pages”, and so on).  A string.|
|kMDItemDescription|description|com.apple.metadata:kMDItemDescription|A description of the content of the resource.  The description may include an abstract, table of contents, reference to a graphical representation of content or a free-text account of the content.  A string.|
|kMDItemDownloadedDate|downloadeddate|com.apple.metadata:kMDItemDownloadedDate|The date the item was downloaded.  A datetime.datetime object.  If datetime.datetime object lacks tzinfo (i.e. it is timezone naive), it will be assumed to be in local timezone.|
|kMDItemDueDate|duedate|com.apple.metadata:kMDItemDueDate|The date the item is due.  A datetime.datetime object.  If datetime.datetime object lacks tzinfo (i.e. it is timezone naive), it will be assumed to be in local timezone.|
|findercolor|findercolor|com.apple.FinderInfo|Color tag set by the Finder.  Colors can also be set by _kMDItemUserTags.  This is controlled by the Finder and it's recommended you don't directly access this attribute.  If you set or remove a color tag via _kMDItemUserTag, osxmetadata will automatically handle processing of FinderInfo color tag.|
|kMDItemFinderComment|findercomment|com.apple.metadata:kMDItemFinderComment|Finder comments for this file.  A string.|
|finderinfo|finderinfo|com.apple.FinderInfo|Info set by the Finder, for example tag color.  Colors can also be set by _kMDItemUserTags.  com.apple.FinderInfo is controlled by the Finder and it's recommended you don't directly access this attribute.  If you set or remove a color tag via _kMDItemUserTag, osxmetadata will automatically handle processing of FinderInfo color tag.|
|kMDItemHeadline|headline|com.apple.metadata:kMDItemHeadline|A publishable entry providing a synopsis of the contents of the file.  A string.|
|kMDItemKeywords|keywords|com.apple.metadata:kMDItemKeywords|Keywords associated with this file. For example, “Birthday”, “Important”, etc. This differs from Finder tags (_kMDItemUserTags) which are keywords/tags shown in the Finder and searchable in Spotlight using "tag:tag_name".  A list of strings.|
|kMDItemParticipants|participants|com.apple.metadata:kMDItemParticipants|The list of people who are visible in an image or movie or written about in a document. A list of strings.|
|kMDItemProjects|projects|com.apple.metadata:kMDItemProjects|The list of projects that this file is part of. For example, if you were working on a movie all of the files could be marked as belonging to the project “My Movie”. A list of strings.|
|kMDItemStarRating|rating|com.apple.metadata:kMDItemStarRating|User rating of this item. For example, the stars rating of an iTunes track. An integer.|
|kMDItemFSIsStationery|stationary|com.apple.metadata:kMDItemFSIsStationery|Boolean indicating if this file is stationery.|
|_kMDItemUserTags|tags|com.apple.metadata:_kMDItemUserTags|Finder tags; searchable in Spotlight using "tag:tag_name".  If you want tags/keywords visible in the Finder, use this instead of kMDItemKeywords.  A list of Tag objects.|
|kMDItemVersion|version|com.apple.metadata:kMDItemVersion|The version number of this file. A string.|
|kMDItemWhereFroms|wherefroms|com.apple.metadata:kMDItemWhereFroms|Describes where the file was obtained from (e.g. URL downloaded from).  A list of strings.|

## Example uses of the package

### Using the command line tool to set metadata:

Set Finder tags to Test, append "John Doe" to list of authors, clear (delete) description, set finder comment to "Hello World":

`osxmetadata --set tags Test --append authors "John Doe" --clear description --set findercomment "Hello World" ~/Downloads/test.jpg`

Set Finder tag Foo with color green:

`osxmetadata --set tags Foo,green test.txt`

Walk a directory tree and add the Finder tag "test" to every file:

`osxmetadata --append tags "Test" --walk ~/Downloads`

Walk a directory tree and add the Finder tag "project" to all .jpg and .pdf files:

`osxmetadata --append tags "project" --walk projectdir --pattern "*.pdf" --pattern "*.jpg"`

### Using the programmatic interface

There are two ways to access metadata using the programmatic interface.  First, an OSXMetaData object will create properties for each supported attribute using the "Short name" in table above.  For example:

```python
from osxmetadata import OSXMetaData, Tag

filename = 'foo.txt'
meta = OSXMetaData(filename)

# set description
meta.description = "This is my document."

# add "Foo" to tags
meta.tags += [Tag("Foo")]

# set authors to "John Doe" and "Jane Smith"
meta.authors = ["John Doe","Jane Smith"]

# clear copyright
meta.copyright = None

```

For additional details on using Finder tags, see [Tag object](#tag-object).

If attribute is a list, most `list` methods can be used. For example:

```python
>>> from osxmetadata import OSXMetaData, Tag
>>> md = OSXMetaData("test.txt")
>>> md.tags
[Tag('Blue', 4), Tag('Green', 2), Tag('Foo', 0)]
>>> md.tags.pop(1)
Tag('Green', 2)
>>> md.tags
[Tag('Blue', 4), Tag('Foo', 0)]
>>> md.tags.sort()
>>> md.tags
[Tag('Blue', 4), Tag('Foo', 0)]
>>> md.tags.append(Tag("Test"))
>>> md.tags
[Tag('Blue', 4), Tag('Foo', 0), Tag('Test', 0)]
>>> md.tags.extend([Tag("Test1"),Tag("Test2")])
>>> md.tags
[Tag('Blue', 4), Tag('Foo', 0), Tag('Test', 0), Tag('Test1', 0), Tag('Test2', 0)]
>>> md.tags.remove(Tag("Blue", 4))
>>> md.tags
[Tag('Foo', 0), Tag('Test', 0), Tag('Test1', 0), Tag('Test2', 0)]
>>> md.tags.remove(Tag("Blue", 4))
# ValueError if attempt to remove element not in list
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/rhet/anaconda3/envs/osxmeta/lib/python3.8/_collections_abc.py", line 997, in remove
    del self[self.index(value)]
  File "/Users/rhet/anaconda3/envs/osxmeta/lib/python3.8/_collections_abc.py", line 911, in index
    raise ValueError
ValueError
>>> md.tags.count(Tag("Test"))
1
>>> md.tags.index(Tag("Test"))
1
```

If attribute is a date/time stamp (e.g. kMDItemDownloadedDate), value should be a `datetime.datetime` object (or a list of `datetime.datetime` objects depending on the attribute type).  

**Note**:  `datetime.datetime` objects may be naive (lack timezone info, e.g. `tzinfo=None`) or timezone aware (have an associated timezone). If `datetime.datetime` object lacks timezone info, it will be assumed to be local time.  MacOS stores date values in extended attributes as UTC timestamps so all `datetime.datetime` objects will undergo appropriate conversion prior to writing to the extended attribute. See also [tz_aware](#tz_aware).

```python
>>> import osxmetadata
>>> md = osxmetadata.OSXMetaData("/Users/rhet/Downloads/test.zip")
>>> md.downloadeddate
[datetime.datetime(2020, 4, 14, 17, 51, 59, 40504)]
>>> now = datetime.datetime.now()
>>> md.downloadeddate = now
>>> md.downloadeddate
[datetime.datetime(2020, 4, 15, 22, 17, 0, 558471)]
```

If attribute is string, it can be treated as a standard python `str`:

```python
>>> import osxmetadata
>>> md = osxmetadata.OSXMetaData("/Users/rhet/Downloads/test.jpg")
>>> md.findercomment = "Hello world"
>>> md.findercomment
'Hello world'
>>> md.findercomment += ". Goodbye"
>>> md.findercomment
'Hello world. Goodbye'
>>> "world" in md.findercomment
True
```


The second way to access metadata is using methods from OSXMetaData to get/set/update etc. the various attributes.  The various methods take the name of the attribute to be operated on which can be specified using either the short name, constant, or long constant from the table above. `osxmetadata` also exports constants with the same name as specified in the Apple documentation and the table above, for example, `kMDItemDescription`.

```
from osxmetadata import *

fname = 'foo.txt'
meta = OSXMetaData(fname)

description = meta.get_attribute(kMDItemDescription)

meta.set_attribute(kMDItemCreator,"OSXMetaData")

meta.append_attribute("tags", [Tag("Blue")])

meta.update_attribute("com.apple.metadata:kMDItemKeywords",["Foo"])

meta.append_attribute("findercomment","Goodbye")

meta.clear_attribute("tags")
```


## OSXMetaData methods and attributes

### Create an OSXMetaData object
`md = osxmetadata.OSXMetaData(filename, tz_aware = False)`

- filename: filename to operate on
- tz_aware: (boolean, optional); if True, attributes which return datetime.datetime objects such as kMDItemDownloadedDate will return timezone aware datetime.datetime objects with timezone set to UTC; if False (default), will return timezone naive objects in user's local timezone.  See also [tz_aware](#tz_aware).

Once created, the following methods and attributes may be used to get/set metadata attribute data

### name
`name()`

Returns POSIX path of the file OSXMetaData is operating on.

### get_attribute
`get_attribute(attribute_name)`

Load attribute and return value or None if attribute was not set (for list attributes, returns empty list if not set).

- attribute_name: an osxmetadata Attribute name

### get_attribute_str
`get_attribute_str(attribute_name)`

Returns a string representation of attribute value.  e.g. if attribute is a datedate.datetime object, will format using datetime.isoformat()

- attribute_name: an osxmetadata Attribute name

### set_attribute
`set_attribute(attribute_name, value)`

Write attribute to file with value

- attribute_name: an osxmetadata Attribute name
- value: value to store in attribute

### update_attribute
`update_attribute(attribute_name, value)`

Update attribute with union of itself and value.  This avoids adding duplicate values to attribute. 

- attribute: an osxmetadata Attribute name
- value: value to append to attribute

Note: implementation simply calls `append_attribute` with `update=True`; provided for convenience.

### append_attribute
`append_attribute(attribute_name, value, update=False)`

Append value to attribute.

- attribute_name: an osxmetadata Attribute name
- value: value to append to attribute
- update: (bool) if True, update instead of append (e.g. avoid adding duplicates, default is False)

### remove_attribute
`remove_attribute(attribute_name, value)`

Remove a value from attribute, raise ValueError if attribute does not contain value.  Only applies to multi-valued attributes, otherwise raises TypeError.

- attribute_name: name of OSXMetaData attribute

### discard_attribute
`discard_attribute(attribute_name, value)`

Remove a value from attribute, unlike remove, does not raise exception if attribute does not contain value.  Only applies to multi-valued attributes, otherwise raises TypeError.

- attribute_name: name of OSXMetaData attribute

### clear_attribute
`clear_attribute(attribute_name)`

Clear anttribute (remove it from the file).

- attribute_name: name of OSXMetaData attribute

### list_metadata
`list_metadata()`

List the Apple metadata attributes set on the file.  e.g. those in com.apple.metadata namespace.

### to_json
`to_json()`

Return dict in JSON format with all attributes for this file.  Format is the same as used by the command line --backup/--restore functions.

### asdict
`asdict()`

Returns a dictionary of attribute values for the dictionary object in form:

```python
{'_version': '0.99.6', '_filepath': '/Users/rhet/Desktop/t.txt', '_filename': 't.txt', 'com.apple.metadata:_kMDItemUserTags': [['Hello', 0]], 'com.apple.metadata:kMDItemComment': 'test', 'com.apple.metadata:kMDItemFinderComment': 'Foo'}
```

### tz_aware
`tz_aware`

Property (boolean, default = False).  If True, any attribute that returns a datetime.datetime object will return a timezone aware object.  If False, datetime.datetime attributes will return timezone naive objects.

For example:


```python
>>> import osxmetadata
>>> import datetime
>>> md = osxmetadata.OSXMetaData("/Users/rhet/Downloads/test.zip")
>>> md.downloadeddate
[datetime.datetime(2020, 4, 14, 17, 51, 59, 40504)]
>>> now = datetime.datetime.now()
>>> md.downloadeddate = now
>>> md.downloadeddate
[datetime.datetime(2020, 4, 15, 22, 17, 0, 558471)]
>>> md.tz_aware = True
>>> md.downloadeddate
[datetime.datetime(2020, 4, 16, 5, 17, 0, 558471, tzinfo=datetime.timezone.utc)]
>>> utc = datetime.datetime.utcnow()
>>> utc
datetime.datetime(2020, 4, 16, 5, 25, 10, 635417)
>>> utc = utc.replace(tzinfo=datetime.timezone.utc)
>>> utc
datetime.datetime(2020, 4, 16, 5, 25, 10, 635417, tzinfo=datetime.timezone.utc)
>>> md.downloadeddate = utc
>>> md.downloadeddate
[datetime.datetime(2020, 4, 16, 5, 25, 10, 635417, tzinfo=datetime.timezone.utc)]
>>> md.tz_aware = False
>>> md.downloadeddate
[datetime.datetime(2020, 4, 15, 22, 25, 10, 635417)]
```

## Tag object

Unlike other attributes, Finder tags (`_kMDItemUserTags`) have two components: a name (str) and a color ID (unsigned int in range 0 to 7) represting a color tag in the Finder.  Reading tags returns a list of `Tag` objects and setting tags requires a list of `Tag` objects.  

### Create a Tag object

`Tag(name,color)`
- `name`: tag name (str)
- `color`: optional; color ID for Finder color label associated with tag (int) 

If color is not provided, `Tag` will see if the user has already assigned a color to a tag of the same name via the Finder (Finder | Preferences | Tags) and if so, assign the same color.  If a match is not found, the tag will be created with no color (`osxmetadata.FINDER_COLOR_NONE`)

Valid color constants (exported by osxmetadata):

- `FINDER_COLOR_GRAY` = 1
- `FINDER_COLOR_GREEN` = 2
- `FINDER_COLOR_PURPLE` = 3
- `FINDER_COLOR_BLUE` = 4
- `FINDER_COLOR_YELLOW` = 5
- `FINDER_COLOR_RED` = 6
- `FINDER_COLOR_ORANGE` = 7


```python
from osxmetadata import OSXMetaData, Tag, FINDER_COLOR_GREEN
md = OSXMetaData("test.txt")
md.tags = [Tag("Foo")]
md.tags += [Tag("Test",FINDER_COLOR_GREEN)]
```

## Usage Notes

Changes are immediately written to the file.  For example, OSXMetaData.tags.append("Foo") immediately writes the tag 'Foo' to the file.

Metadata is refreshed from disk every time a class property is accessed.

This will only work on file systems that support Mac OS X extended attributes.

## Dependencies
[bitstring](https://pypi.org/project/bitstring/)

[Click](https://palletsprojects.com/p/click/)

[PyObjC](https://pythonhosted.org/pyobjc/)

[xattr](https://github.com/xattr/xattr)

[py-applescript](https://github.com/rdhyee/py-applescript)

## Related Projects

- [tag](https://github.com/jdberry/tag) A command line tool to manipulate tags on Mac OS X files, and to query for files with those tags.
- [osx-tags](https://github.com/scooby/osx-tags) Python module to manipulate Finder tags in OS X.

## Acknowledgements
This module was inspired by [osx-tags](https://github.com/scooby/osx-tags) by "Ben S / scooby".  I leveraged osx-tags to bootstrap the design of this module.  I wanted a more general OS X metadata library so I rolled my own.  This module is published under the same MIT license as osx-tags.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="http://www.borja.glezseoane.es"><img src="https://avatars.githubusercontent.com/u/24481419?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Borja González Seoane</b></sub></a><br /><a href="https://github.com/RhetTbull/osxmetadata/commits?author=bglezseoane" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
