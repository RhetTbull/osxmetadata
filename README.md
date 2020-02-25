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
  -v, --version             Show the version and exit.
  -w, --walk                Walk directory tree, processing each file in the
                            tree
  --set ATTRIBUTE VALUE     Set ATTRIBUTE to VALUE
  --list                    List all metadata attributes for FILE
  --clear ATTRIBUTE         Remove attribute from FILE
  --append ATTRIBUTE VALUE  Append VALUE to ATTRIBUTE
  --get ATTRIBUTE           Get value of ATTRIBUTE
  --remove ATTRIBUTE VALUE  Remove VALUE from ATTRIBUTE; only applies to
                            multi-valued attributes
  --update ATTRIBUTE VALUE  Update ATTRIBUTE with VALUE; for multi-valued
                            attributes, this adds VALUE to the attribute if
                            not already in the list
  --help                    Show this message and exit.

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
                author, or authors, of the contents of the file. An array of
                strings.
comment         kMDItemComment, com.apple.metadata:kMDItemComment; A comment
                related to the file. This differs from the Finder comment,
                kMDItemFinderComment. A string.
copyright       kMDItemCopyright, com.apple.metadata:kMDItemCopyright; The
                copyright owner of the file contents. A string.
creator         kMDItemCreator, com.apple.metadata:kMDItemCreator;
                Application used to create the document content (for example
                “Word”, “Pages”, and so on). A string.
description     kMDItemDescription, com.apple.metadata:kMDItemDescription; A
                description of the content of the resource. The description
                may include an abstract, table of contents, reference to a
                graphical representation of content or a free-text account
                of the content. A string.
downloadeddate  kMDItemDownloadedDate,
                com.apple.metadata:kMDItemDownloadedDate; The date the item
                was downloaded.  A date in ISO 8601 format: e.g.
                2000-01-12T12:00:00 or 2000-12-31 (ISO 8601 w/o time zone)
findercomment   kMDItemFinderComment,
                com.apple.metadata:kMDItemFinderComment; Finder comments for
                this file. A string.
headline        kMDItemHeadline, com.apple.metadata:kMDItemHeadline; A
                publishable entry providing a synopsis of the contents of
                the file. A string.
keywords        kMDItemKeywords, com.apple.metadata:kMDItemKeywords;
                Keywords associated with this file. For example, “Birthday”,
                “Important”, etc. This differs from Finder tags
                (_kMDItemUserTags) which are keywords/tags shown in the
                Finder and searchable in Spotlight using "tag:tag_name"An
                array of strings.
tags            _kMDItemUserTags, com.apple.metadata:_kMDItemUserTags;
                Finder tags; searchable in Spotlight using "tag:tag_name".
                If you want tags/keywords visible in the Finder, use this
                instead of kMDItemKeywords.
wherefroms      kMDItemWhereFroms, com.apple.metadata:kMDItemWhereFroms;
                Describes where the file was obtained from (e.g. URL
                downloaded from). An array of strings.
```


## Supported Attributes

Information about commonly used MacOS metadata attributes is available from [Apple](https://developer.apple.com/documentation/coreservices/file_metadata/mditem/common_metadata_attribute_keys?language=objc).  

`osxmetadata` currently supports the following metadata attributes:

| Constant | Short Name | Long Constant | Description |
|---------------|----------|---------|-----------|
|kMDItemAuthors|authors|com.apple.metadata:kMDItemAuthors|The author, or authors, of the contents of the file. An array of strings.|
|kMDItemComment|comment|com.apple.metadata:kMDItemComment|A comment related to the file. This differs from the Finder comment, kMDItemFinderComment. A string.|
|kMDItemCopyright|copyright|com.apple.metadata:kMDItemCopyright|The copyright owner of the file contents. A string.|
|kMDItemCreator|creator|com.apple.metadata:kMDItemCreator|Application used to create the document content (for example “Word”, “Pages”, and so on). A string.|
|kMDItemDescription|description|com.apple.metadata:kMDItemDescription|A description of the content of the resource. The description may include an abstract, table of contents, reference to a graphical representation of content or a free-text account of the content. A string.|
|kMDItemDownloadedDate|downloadeddate|com.apple.metadata:kMDItemDownloadedDate|The date the item was downloaded.  A date in ISO 8601 format: e.g. 2000-01-12T12:00:00 or 2000-12-31 (ISO 8601 w/o time zone)|
|kMDItemFinderComment|findercomment|com.apple.metadata:kMDItemFinderComment|Finder comments for this file. A string.|
|kMDItemHeadline|headline|com.apple.metadata:kMDItemHeadline|A publishable entry providing a synopsis of the contents of the file. A string.|
|kMDItemKeywords|keywords|com.apple.metadata:kMDItemKeywords|Keywords associated with this file. For example, “Birthday”, “Important”, etc. This differs from Finder tags (_kMDItemUserTags) which are keywords/tags shown in the Finder and searchable in Spotlight using "tag:tag_name"An array of strings.|
|_kMDItemUserTags|tags|com.apple.metadata:_kMDItemUserTags|Finder tags; searchable in Spotlight using "tag:tag_name".  If you want tags/keywords visible in the Finder, use this instead of kMDItemKeywords.|
|kMDItemWhereFroms|wherefroms|com.apple.metadata:kMDItemWhereFroms|Describes where the file was obtained from (e.g. URL downloaded from). An array of strings.|


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

# add "Foo" to tags but not if tags already contains "Foo"
meta.tags.update("Foo")

# set authors to "John Doe" and "Jane Smith"
meta.authors = ["John Doe","Jane Smith"]

# clear copyright
meta.copyright = None

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

#### Tags

Accessed via OSXMetaData.tags.  Represents Finder tags (_kMDItemUserTags).

Behaves mostly like a set with following methods:

* update (sets multiple tags)
* add (add a single tag)
* += (add a single tag)
* remove (raises error if tag not present)
* discard (does not raise error if tag not present)
* clear (removes all tags)

To replace all tags with a new set of tags, use clear() then update()

Duplicate tags will be ignored.

The standard OS X Finder color labels are handled via tags.  For example, setting a tag name of Gray, Green, Purple, Blue, Yellow, Red, or Orange will also set the equivalent Finder color label. This is consistent with how the Finder works.  If a file has a color label, it will be returned as a tag of the corresponding color name when reading from OSXMetaData.tags

```python
>>> from osxmetadata import OSXMetaData
>>> md = OSXMetaData('foo.txt')
>>> md.tags.update('Foo','Gray','Red','Test')
>>> print(md.tags)
Foo, Gray, Red, Test
#Standard Mac Finder color labels are normalized
>>> md.tags.add('PURPLE')
>>> print(md.tags)
Foo, Purple, Red, Test, Gray
>>> md.tags.add('FOOBAR')
>>> print(md.tags)
Foo, Purple, Red, Test, Gray, FOOBAR
>>> md.tags += 'MyCustomTag'
>>> print(md.tags)
Foo, Purple, Red, Test, Gray, MyCustomTag, FOOBAR
>>> md.tags.remove('Purple')
>>> print(md.tags)
Foo, Red, Test, Gray, MyCustomTag, FOOBAR
>>> md.tags.remove('Purple')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "osxmetadata/osxmetadata.py", line 148, in remove
    tags.remove(self.__tag_normalize(tag))
KeyError: 'Purple\n3'
>>> md.tags.discard('Purple')
>>> md.tags.discard('Red')
>>> print(md.tags)
Foo, Test, Gray, MyCustomTag, FOOBAR
>>> len(md.tags)
5
>>> md.tags.clear()
>>> print(md.tags)

>>> len(md.tags)
0
>>>
```

## Usage Notes

Changes are immediately written to the file.  For example, OSXMetaData.tags.add("Foo") immediately writes the tag 'Foo' to the file.

Metadata is refreshed from disk every time a class property is accessed.

This will only work on file systems that support Mac OS X extended attributes.

## Dependencies
[PyObjC](https://pythonhosted.org/pyobjc/)

[xattr](https://github.com/xattr/xattr)

## Acknowledgements
This module was inspired by [osx-tags]( https://github.com/scooby/osx-tags) by "Ben S / scooby".  I leveraged osx-tags to bootstrap the design of this module.  I wanted a more
general OS X metadata library so I rolled my own.  This module is published under the same MIT license as osx-tags.


To set the Finder comments, I use [py-applescript]( https://github.com/rdhyee/py-applescript) by "Raymond Yee / rdhyee".  Rather than import this module, I included the entire module
(which is published as public domain code) in a private module to prevent ambiguity with
other applescript modules on PyPi.  py-applescript uses a native bridge via PyObjC and
is very fast compared to the other osascript based modules.
