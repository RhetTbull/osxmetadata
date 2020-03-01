# osxmetadata 

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## What is osxmetadata?

osxmetadata provides a simple interface to access various metadata about MacOS / OS X files.  Currently supported metadata attributes include tags/keywords, Finder comments, authors, etc.  

## Motivation

Apple provides rich support for file metadata through various metadata extended attributes.  MacOS provides tools to view and set these various metadata attributes.  For example, `mdls` lists metadata associated with a file but doesn't let you edit the data while `xattr` allows the user to set extended attributes but requires the values be in the form of a MacOS plist which is impractical.   `osxmetadata` makes it easy to to both view and manipulate the MacOS metadata attributes, either programmatically or through a command line tool.

## Supported operating systems

Only works on MacOS.  Requires Python 3.6+. 

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
  -w, --walk                      Walk directory tree, processing each file in
                                  the tree
  -j, --json                      Print output in JSON format, for use with
                                  --list and --get.
  --set ATTRIBUTE VALUE           Set ATTRIBUTE to VALUE
  --list                          List all metadata attributes for FILE
  --clear ATTRIBUTE               Remove attribute from FILE
  --append ATTRIBUTE VALUE        Append VALUE to ATTRIBUTE
  --get ATTRIBUTE                 Get value of ATTRIBUTE
  --remove ATTRIBUTE VALUE        Remove VALUE from ATTRIBUTE; only applies to
                                  multi-valued attributes
  --update ATTRIBUTE VALUE        Update ATTRIBUTE with VALUE; for multi-
                                  valued attributes, this adds VALUE to the
                                  attribute if not already in the list
  --mirror ATTRIBUTE1 ATTRIBUTE2  Mirror values between ATTRIBUTE1 and
                                  ATTRIBUTE2 so that ATTRIBUTE1 = ATTRIBUTE2;
                                  for multi-valued attributes, merges values;
                                  for string attributes, sets ATTRIBUTE1 =
                                  ATTRIBUTE2 overwriting any value in
                                  ATTRIBUTE1.  For example: '--mirror keywords
                                  tags' sets tags and keywords to same values
  --backup                        Backup FILE attributes.  Backup file
                                  '.osxmetadata.json' will be created in same
                                  folder as FILE
  --restore                       Restore FILE attributes from backup file.
                                  Restore will look for backup file
                                  '.osxmetadata.json' in same folder as FILE
  -V, --verbose                   Print verbose output
  --help                          Show this message and exit.

Valid attributes for ATTRIBUTE: Each attribute has a short name, a constant
name, and a long constant name. Any of these may be used for ATTRIBUTE

For example: --set findercomment "Hello world"
or:          --set kMDFinderComment "Hello world"
or:          --set com.apple.metadata:kMDItemFinderComment "Hello world"

Attributes that are strings can only take one value for --set; --append will
append to the existing value.  Attributes that are arrays can be set multiple
times to add to the array: e.g. --set keywords 'foo' --set keywords 'bar' will
set keywords to ['foo', 'bar']

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
                was downloaded.  A date in ISO 8601 format: e.g.
                2000-01-12T12:00:00 or 2000-12-31 (ISO 8601 w/o time zone)
findercomment   kMDItemFinderComment,
                com.apple.metadata:kMDItemFinderComment; Finder comments for
                this file.  A string.
headline        kMDItemHeadline, com.apple.metadata:kMDItemHeadline; A
                publishable entry providing a synopsis of the contents of
                the file.  A string.
keywords        kMDItemKeywords, com.apple.metadata:kMDItemKeywords;
                Keywords associated with this file. For example, “Birthday”,
                “Important”, etc. This differs from Finder tags
                (_kMDItemUserTags) which are keywords/tags shown in the
                Finder and searchable in Spotlight using "tag:tag_name".  A
                list of strings.
tags            _kMDItemUserTags, com.apple.metadata:_kMDItemUserTags;
                Finder tags; searchable in Spotlight using "tag:tag_name".
                If you want tags/keywords visible in the Finder, use this
                instead of kMDItemKeywords.  A list of strings.
wherefroms      kMDItemWhereFroms, com.apple.metadata:kMDItemWhereFroms;
                Describes where the file was obtained from (e.g. URL
                downloaded from).  A list of strings.
```


## Supported Attributes

Information about commonly used MacOS metadata attributes is available from [Apple](https://developer.apple.com/documentation/coreservices/file_metadata/mditem/common_metadata_attribute_keys?language=objc).  

`osxmetadata` currently supports the following metadata attributes:

| Constant | Short Name | Long Constant | Description |
|---------------|----------|---------|-----------|
|kMDItemAuthors|authors|com.apple.metadata:kMDItemAuthors|The author, or authors, of the contents of the file. A list of strings.|
|kMDItemComment|comment|com.apple.metadata:kMDItemComment|A comment related to the file. This differs from the Finder comment, kMDItemFinderComment. A string.|
|kMDItemCopyright|copyright|com.apple.metadata:kMDItemCopyright|The copyright owner of the file contents. A string.|
|kMDItemCreator|creator|com.apple.metadata:kMDItemCreator|Application used to create the document content (for example “Word”, “Pages”, and so on). A string.|
|kMDItemDescription|description|com.apple.metadata:kMDItemDescription|A description of the content of the resource. The description may include an abstract, table of contents, reference to a graphical representation of content or a free-text account of the content. A string.|
|kMDItemDownloadedDate|downloadeddate|com.apple.metadata:kMDItemDownloadedDate|The date the item was downloaded.  A date in ISO 8601 format: e.g. 2000-01-12T12:00:00 or 2000-12-31 (ISO 8601 w/o time zone)|
|kMDItemFinderComment|findercomment|com.apple.metadata:kMDItemFinderComment|Finder comments for this file. A string.|
|kMDItemHeadline|headline|com.apple.metadata:kMDItemHeadline|A publishable entry providing a synopsis of the contents of the file. A string.|
|kMDItemKeywords|keywords|com.apple.metadata:kMDItemKeywords|Keywords associated with this file. For example, “Birthday”, “Important”, etc. This differs from Finder tags (_kMDItemUserTags) which are keywords/tags shown in the Finder and searchable in Spotlight using "tag:tag_name"A list of strings.|
|_kMDItemUserTags|tags|com.apple.metadata:_kMDItemUserTags|Finder tags; searchable in Spotlight using "tag:tag_name".  If you want tags/keywords visible in the Finder, use this instead of kMDItemKeywords. A list of strings.|
|kMDItemWhereFroms|wherefroms|com.apple.metadata:kMDItemWhereFroms|Describes where the file was obtained from (e.g. URL downloaded from). A list of strings.|


## Example uses of the package

### Using the command line tool to set metadata:

Set Finder tags to Test, append "John Doe" to list of authors, clear (delete) description, set finder comment to "Hello World":

`osxmetadata --set tags Test --append authors "John Doe" --clear description --set findercomment "Hello World" ~/Downloads/test.jpg`

Walk a directory tree and add the Finder tag "test" to every file:

`osxmetadata --append tags "Test" --walk ~/Downloads`

### Using the programmatic interface

There are two ways to access metadata using the programmatic interface.  First, an OSXMetaData object will create properties for each supported attribute using the "Short name" in table above.  For example:

```python
from osxmetadata import OSXMetaData

filename = 'foo.txt'
meta = OSXMetaData(filename)

# set description
meta.description = "This is my document."

# add "Foo" to tags
meta.tags += ["Foo"]

# set authors to "John Doe" and "Jane Smith"
meta.authors = ["John Doe","Jane Smith"]

# clear copyright
meta.copyright = None

```

If attribute is a list, most `list` methods can be used. For example:

```python
>>> import osxmetadata
>>> md = osxmetadata.OSXMetaData("/Users/rhet/Downloads/test.jpg")
>>> md.tags
['Blue', 'Green', 'Foo']
>>> md.tags.reverse()
>>> md.tags
['Foo', 'Green', 'Blue']
>>> md.tags.pop(1)
'Green'
>>> md.tags
['Foo', 'Blue']
>>> md.tags.sort()
>>> md.tags
['Blue', 'Foo']
>>> md.tags.append("Test")
>>> md.tags
['Blue', 'Foo', 'Test']
>>> md.tags.extend(["Tag1","Tag2"])
>>> md.tags
['Blue', 'Foo', 'Test', 'Tag1', 'Tag2']
>>> md.tags += ["Tag3"]
>>> md.tags
['Blue', 'Foo', 'Test', 'Tag1', 'Tag2', 'Tag3']
>>> md.tags.remove('Blue')
>>> md.tags
['Foo', 'Test', 'Tag1', 'Tag2', 'Tag3']
>>> # removing value that doesn't exist raises ValueError
>>> md.tags.remove('Blue')
Traceback (most recent call last):
...
ValueError: list.remove(x): x not in list
>>> md.tags
['Foo', 'Test', 'Tag1', 'Tag2', 'Tag3']
>>> md.tags.count('Test')
1
>>> md.tags.index('Tag1')
2
```

If attribute is a date/time stamp (e.g. kMDItemDownloadedDate), value should be a `datetime.datetime` object (or a list of `datetime.datetime` objects depending on the attribute type):

```python
>>> import osxmetadata
>>> import datetime
>>> md = osxmetadata.OSXMetaData("/Users/rhet/Downloads/test.jpg")
>>> md.downloadeddate
[datetime.datetime(2012, 2, 13, 0, 0)]
>>> md.downloadeddate = [datetime.datetime.now()]
>>> md.downloadeddate
[datetime.datetime(2020, 2, 29, 8, 36, 10, 332350)]
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

meta.append_attribute("tags",["Blue"])

meta.update_attribute("com.apple.metadata:kMDItemKeywords",["Foo"])

meta.append_attribute("findercomment","Goodbye")

meta.clear_attribute("tags")
```

## Programmatic Interface:

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

## Usage Notes

Changes are immediately written to the file.  For example, OSXMetaData.tags.append("Foo") immediately writes the tag 'Foo' to the file.

Metadata is refreshed from disk every time a class property is accessed.

This will only work on file systems that support Mac OS X extended attributes.

## Dependencies
[PyObjC](https://pythonhosted.org/pyobjc/)

[xattr](https://github.com/xattr/xattr)

[Click](https://palletsprojects.com/p/click/)

## Acknowledgements
This module was inspired by [osx-tags]( https://github.com/scooby/osx-tags) by "Ben S / scooby".  I leveraged osx-tags to bootstrap the design of this module.  I wanted a more general OS X metadata library so I rolled my own.  This module is published under the same MIT license as osx-tags.


To set the Finder comments, I use [py-applescript]( https://github.com/rdhyee/py-applescript) by "Raymond Yee / rdhyee".  Rather than import this module, I included the entire module (which is published as public domain code) in a private module to prevent ambiguity with other applescript modules on PyPi.  py-applescript uses a native bridge via PyObjC and is very fast compared to the other osascript based modules.
