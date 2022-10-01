# osxmetadata

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![All Contributors](https://img.shields.io/badge/all_contributors-2-orange.svg?style=flat)](#contributors-)

## What is osxmetadata?

osxmetadata provides a simple interface to access various metadata about MacOS / OS X files.  Currently supported metadata attributes include tags/keywords, Finder comments, authors, etc.

## Why osxmetadata?

Apple provides rich support for file metadata through the [MDItem](https://developer.apple.com/documentation/coreservices/file_metadata/mditem) class and the [NSURL getResourceValue:forKey:error:](https://developer.apple.com/documentation/foundation/nsurl/1408874-getresourcevalue?language=objc) method. However, Apple does not provide a way to easily set much of the metadata. For example, while there is a documented [MDItem MDItemCopyAttribute](https://developer.apple.com/documentation/coreservices/1427080-mditemcopyattribute?language=objc) to copy metadata attributes such as [kMDItemAuthors](https://developer.apple.com/documentation/coreservices/kmditemauthors?language=objc), Apple does not provide a public interface to set this data.  Other data, such as Finder comments, can only be set through sending AppleScript commands to the Finder and others, like Finder tags can be retrieved but cannot be set through the public API.

osxmetadata provides a unified interface to get and set most of the metadata available on your Mac from python.  It uses a combination of documented and undocumented APIs to access the metadata.  It also provides a simple interface to set Finder tags and Finder comments.

MacOS provides some tools to view these various metadata attributes.  For example, `mdls` lists the MDItem Spotlight metadata associated with a file but doesn't let you edit the data. osxmetadata makes it easy to to both view and manipulate the macOS metadata attributes, either programmatically or through an included `osxmetadata` command line tool.

## Supported operating systems

Only works on MacOS.  Requires Python 3.8+. Tested on macOS 10.15.7 (Catalina); should work on all versions of macOS 10.15 and later.

## Installation instructions

### Installation using pipx

If you aren't familiar with installing python applications, I recommend you install `osxmetadata` with [pipx](https://github.com/pipxproject/pipx). If you use `pipx`, you will not need to create a virtual environment as `pipx` takes care of this. The easiest way to do this on a Mac is to use [homebrew](https://brew.sh/):

- Open `Terminal` (search for `Terminal` in Spotlight or look in `Applications/Utilities`)
- Install `homebrew` according to instructions at [https://brew.sh/](https://brew.sh/)
- Type the following into Terminal: `brew install pipx`
- Then type this: `pipx install osxmetadata`
- Now you should be able to run `osxmetadata` by typing: `osxmetadata`

Once you've installed osxmetadata with pipx, to upgrade to the latest version:

    pipx upgrade osxmetadata

### Installation using pip

You can also install directly from [pypi](https://pypi.org/project/osxmetadata/):

    pip install osxmetadata

Once you've installed osxmetadata with pip, to upgrade to the latest version:

    pip install --upgrade osxmetadata

### Installation from git repository

OSXMetaData uses setuptools, thus simply run:

    git clone https://github.com/RhetTbull/osxmetadata.git
    cd osxmetadata 
    python3 setup.py install

I recommend you create a [virtual environment](https://docs.python.org/3/tutorial/venv.html) before installing osxmetadata.

## Using the API

```pycon
>>> from osxmetadata import *
>>> import datetime
>>> md = OSXMetaData("test_file.txt")
>>> md.set(kMDItemAuthors, ["Jane Smith", "John Doe"])
>>> md.get(kMDItemAuthors)
['Jane Smith', 'John Doe']
>>> md.kMDItemFinderComment = "This is my comment"
>>> md.kMDItemFinderComment
'This is my comment'
>>> md.tags = [Tag("Test", FINDER_COLOR_NONE), Tag("ToDo", FINDER_COLOR_RED)]
>>> md.tags
[Tag(name='Test', color=0), Tag(name='ToDo', color=6)]
>>> md[kMDItemDueDate] = datetime.datetime(2022,10,1)
>>> md[kMDItemDueDate]
datetime.datetime(2022, 10, 1, 0, 0)
>>>
```

Somewhat contrary to the [Zen of Python](https://peps.python.org/pep-0020/), osxmetadata provides more than one way to access metadata attributes.  You can get and set metadata attributes using the `get()`/`set()` getter/setter methods, using the attribute name as a dictionary key on the OSXMetaData object, or using the attribute name as an attribute on the `OSXMetaData()` object.  For example, the following are all equivalent:

- `OSXMetaData.get(attribute)` - get the value of the metadata attribute `attribute`
- `OSXMetaData[attribute]` - get the value of the metadata attribute `attribute`
- `OSXMetaData.attribute` - get the value of the metadata attribute `attribute`

As are the following:

- `OSXMetaData.set(attribute, value)` - set the value of the metadata attribute `attribute` to `value`
- `OSXMetaData[attribute] = value` - set the value of the metadata attribute `attribute` to `value`
- `OSXMetaData.attribute = value` - set the value of the metadata attribute `attribute` to `value`

This allows you to use osxmetadata in accordance with your own code style preferences.

Supported attribute names include all attributes defined for [MDItem](https://developer.apple.com/documentation/coreservices/file_metadata/mditem) and all resource keys defined for [NSURL](https://developer.apple.com/documentation/foundation/nsurl?language=objc) as well as the following additional attributes:

- `_kMDItemUserTags` - list of Finder tags
- `kMDItemDownloadedDate` - date the file was downloaded

Additionally, osxmetadata defines a "shortcut name" attribute for each MDItem attribute that can be used as a shortcut `OSXMetaData` class attribute.  The shortcut name is the lowercase value of text following `kMDItem` for each attribute. For example, `kMDItemAuthors` has a short name of `authors` so you can set the authors like this:

```pycon
>>> from osxmetadata import *
>>> md = OSXMetaData("test_file.txt")
>>> md.authors = ["Jane Smith", "John Doe"]
>>> md.authors
['Jane Smith', 'John Doe']
>>>
```

and `kMDItemDueDate` would have a short name of `duedate`:

```pycon
>>> from osxmetadata import *
>>> import datetime
>>> md = OSXMetaData("test_file.txt")
>>> md.duedate = datetime.datetime(2022, 10, 1)
>>> md.duedate
datetime.datetime(2022, 10, 1, 0, 0)
>>>
```

The names of all supported attributes are available in the `osxmetadata.ALL_ATTRIBUTES` set:

```pycon
>>> from osxmetadata import ALL_ATTRIBUTES
>>> "kMDItemDueDate" in ALL_ATTRIBUTES
True
>>> "NSURLTagNamesKey" in ALL_ATTRIBUTES
True
>>> "findercomment" in ALL_ATTRIBUTES
True
>>>
```

The class attributes are handled dynamically which, unfortunately, means that IDEs like PyCharm and Visual Studio Code cannot provide tab-completion for them.

## Finder Tags

Unlike other attributes, which are mapped to native Python types appropriate for the source Objective C type, Finder tags (`_kMDItemUserTags` or `tags`) have two components: a name (str) and a color ID (unsigned int in range 0 to 7) representing a color tag in the Finder.  Reading tags returns a list of `Tag` namedtuples and setting tags requires a list of `Tag` namedtuples.  

```pycon
>>> from osxmetadata import *
>>> md = OSXMetaData("test_file.txt")
>>> md.tags = [Tag("Test", FINDER_COLOR_NONE), Tag("ToDo", FINDER_COLOR_RED)]
>>> md.tags
[Tag(name='Test', color=0), Tag(name='ToDo', color=6)]
>>> md.get("_kMDItemUserTags")
[Tag(name='Test', color=0), Tag(name='ToDo', color=6)]
>>> 
```

Tag names (but not colors) can also be accessed through the [NSURLTagNamesKey](https://developer.apple.com/documentation/foundation/nsurltagnameskey) resource key and the label color ID is accessible through `NSURLLabelNumberKey`; the localized label color name is accessible through `NSURLLocalizedLabelKey` though these latter two resource keys only return a single color whereas a file may have more than one color tag. For most purposes, I recommend using the `tags` attribute as it is more convenient and provides access to both the name and color ID of the tag.

```pycon
>>> from osxmetadata import *
>>> md = OSXMetaData("test_file.txt")
>>> md.tags = [Tag("Test", FINDER_COLOR_NONE), Tag("ToDo", FINDER_COLOR_RED)]
>>> md.tags
[Tag(name='Test', color=0), Tag(name='ToDo', color=6)]
>>> md.NSURLTagNamesKey
(
    Test,
    ToDo
)
>>> md.NSURLLabelNumberKey
6
>>> md.NSURLLocalizedLabelKey
'Red'
>>> md.NSURLTagNamesKey = ["NewTag"]
>>> md.NSURLTagNamesKey
(
    NewTag
)
>>> md.tags
[Tag(name='NewTag', color=0)]
>>>
```

### Create a Tag namedtuple

`Tag(name, color)`

- `name`: tag name (str)
- `color`: color ID for Finder color label associated with tag (int)

Valid color constants (exported by osxmetadata):

- `FINDER_COLOR_NONE` = 0
- `FINDER_COLOR_GRAY` = 1
- `FINDER_COLOR_GREEN` = 2
- `FINDER_COLOR_PURPLE` = 3
- `FINDER_COLOR_BLUE` = 4
- `FINDER_COLOR_YELLOW` = 5
- `FINDER_COLOR_RED` = 6
- `FINDER_COLOR_ORANGE` = 7

## Finder Comments

Finder comments can be access via the `kMDItemFinderComment` attribute or the `findercomment` shortcut attribute. Apple provides a public API for getting Finder comments but does not provide a programmatic method for setting Finder comments and I have not been able to find a private API for doing so. osxmetadata works around this by send AppleScript events to the Finder to set the Finder comment. This means that setting Finder comments is slower than setting other attributes and may not work in all circumstances. The first time you set a Finder comment, your terminal app may need to prompt you to allow AppleScript to control the Finder. If you include osxmetadata in a standalone app, for example, one created with [py2app](https://py2app.readthedocs.io/en/latest/), you will need to include the `com.apple.security.automation.apple-events` entitlement and the `NSAppleEventsUsageDescription` key in your app's `Info.plist` file. See the [Apple Developer Documentation](https://developer.apple.com/documentation/bundleresources/information_property_list/nsappleeventsusagedescription?language=objc) for more information.

```pycon
>>> from osxmetadata import *
>>> md = OSXMetaData("test_file.txt")
>>> md.kMDItemFinderComment = "Hello World!"
>>> md.kMDItemFinderComment
'Hello World!'
>>> md.findercomment
'Hello World!'
>>>
```

## Dates/Times

Metadata attributes which return date/times such as `kMDItemDueDate` or `kMDItemDownloadedDate` return a `datetime.datetime` object.  The `datetime.datetime` object is timezone-naive (does not contain timezone) and returns the time in the local timezone.  Internally, Apple appears to store these as [CFDate](https://developer.apple.com/documentation/corefoundation/cfdate?language=objc) objects in the UTC timezone but when retrieved, they are returned in the local time.  You may pass a timezone-aware datetime object to set these attributes and it will be converted appropriately.

```pycon
>>> from osxmetadata import *
>>> md = OSXMetaData("test_file.txt")
>>> import datetime
>>> md.kMDItemDueDate = datetime.datetime(2022, 10, 1)
>>> md.kMDItemDueDate
datetime.datetime(2022, 10, 1, 0, 0)
>>> md.kMDItemDownloadedDate = datetime.datetime(2022, 10, 1, tzinfo=datetime.timezone.utc)
>>> 
```

## Extended Attributes

In addition to `MDItem` and `NSURL` metadata attributes, osxmetadata can also read & write metadata saved in extended attributes. For many MDItem attributes, Apple stores the same data in both the MDItem and extended attribute (with name `com.apple.metadata:AttributeName`).  For example, the `kMDItemWhereFroms` attribute can be accessed both via MDItemCopyAttribute (exposed via osxmetadata's `get()` method) and via the `com.apple.metadata:kMDItemWhereFroms` extended attribute.  The extended attribute is a binary plist (BPLIST) and can be read using the `xattr` command line tool.  The `get_xattr()` method will return the value of the extended attribute and the `set_xattr()` method will set it.  Extended attributes can be removed with the `remove_xattr()` method.  `get_xattr()` provides for an optional callable argument, `decode`, which will be called on the returned value.  `set_xattr()` provides an optional callable argument `encode`. This is useful for encoding/decoding binary plist data.  For example, to decode the `com.apple.metadata:kMDItemWhereFroms` extended attribute, you can use the `plistlib.loads()` function:

```pycon
>>> from osxmetadata import *
>>> import plistlib
>>> from plistlib import FMT_BINARY
>>> from functools import partial
>>> md = OSXMetaData("test_file.txt")
>>> md.kMDItemWhereFroms = ["apple.com"]
>>> md.kMDItemWhereFroms
['apple.com']
>>> decode = partial(plistlib.loads, fmt=FMT_BINARY)
>>> encode = partial(plistlib.dumps, fmt=FMT_BINARY)
>>> md.get_xattr("com.apple.metadata:kMDItemWhereFroms")
b'bplist00\xa1\x01Yapple.com\x08\n\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x14'
>>> md.get_xattr("com.apple.metadata:kMDItemWhereFroms", decode=decode)
['apple.com']
>>> md.set_xattr("com.apple.metadata:kMDItemWhereFroms", ["google.com"], encode=encode)
>>> md.get_xattr("com.apple.metadata:kMDItemWhereFroms", decode=decode)
['google.com']
>>> md.remove_xattr("com.apple.metadata:kMDItemWhereFroms")
>>>
```

For most use cases, it is recommended you do not directly access the Apple metadata related extended attributes and instead use the getter/setter methods provided by osxmetadata.

## Command Line Usage

Installs command line tool called `osxmetadata` which provides a simple interface to view/edit metadata supported by osxmetadata.

If you only care about the command line tool, I recommend installing with [pipx](https://github.com/pipxproject/pipx)

The command line tool can also be run via `python -m osxmetadata`.  Running it with no arguments or with --help option will print a help message:

```

TODO: put text here

```

## Notes on backup/restore

When run with `--backup`, osxmetadata backs up the metadata of each file in a file called `.osxmetadata.json`. A backup file is created in every directory that includes files being backup up. The format is plain JSON text with a record for each file that was backed up. If you delete a file then run the `--backup` again, the deleted file's record is not deleted from the `.osxmetadata.json` backup file. The backup file is kept in each directory/sub-directory and only the filename is used for `--restore` which means you can move/rename the directory (along with the `.osxmetadata.json` file) and the restore will still work correctly.

**Note**: Prior to version 0.99.38, the backup file was not well-formed JSON which meant that some apps/viewers could not process the JSON file.  Version 0.99.38 fixes this and will silently update any `.osxmetadata.json` file encountered during `--backup` to be well-formed JSON but this breaks backwards compatibility with older versions of osxmetadata. If you use osxmetadata to sync data across multiple Macs, you must ensure all Macs are running the updated version.  For additional details, see [issue #57](https://github.com/RhetTbull/osxmetadata/issues/57).

## Usage Notes

This will only work on file systems that support Mac OS X extended attributes.

## Related Projects

- [tag](https://github.com/jdberry/tag) A command line tool to manipulate tags on Mac OS X files, and to query for files with those tags.
- [osx-tags](https://github.com/scooby/osx-tags) Python module to manipulate Finder tags in OS X.

## Acknowledgements

This module was inspired by [osx-tags](https://github.com/scooby/osx-tags) by "Ben S / scooby".  I leveraged osx-tags to bootstrap the design of this module.  I wanted a more general OS X metadata library so I rolled my own.  This module is published under the same MIT license as osx-tags.

## License

MIT License

Copyright (c) 2020 Rhet Turnbull

## Contributing

Contributions of all kinds are welcome.  Please submit a pull request or open an issue.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="http://www.borja.glezseoane.es"><img src="https://avatars.githubusercontent.com/u/24481419?v=4?s=75" width="75px;" alt=""/><br /><sub><b>Borja González Seoane</b></sub></a><br /><a href="https://github.com/RhetTbull/osxmetadata/commits?author=bglezseoane" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/porg"><img src="https://avatars.githubusercontent.com/u/737143?v=4?s=75" width="75px;" alt=""/><br /><sub><b>porg</b></sub></a><br /><a href="https://github.com/RhetTbull/osxmetadata/issues?q=author%3Aporg" title="Bug reports">🐛</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
