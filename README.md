# osxmetadata

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![All Contributors](https://img.shields.io/badge/all_contributors-5-orange.svg?style=flat)](#contributors-)

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
    pip install poetry
    poetry install

I recommend you create a [virtual environment](https://docs.python.org/3/tutorial/venv.html) before installing osxmetadata.

## Using the API

```pycon
>>> import datetime
>>> import pathlib
>>> from osxmetadata import *
>>> pathlib.Path("test_file.txt").touch()
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

Supported attribute names include all attributes defined for [MDItem](https://developer.apple.com/documentation/coreservices/file_metadata/mditem) and all resource keys defined for [NSURL](https://developer.apple.com/documentation/foundation/nsurl?language=objc). Additionally, the metadata constants defined in the [MDImporter](https://developer.apple.com/documentation/coreservices/file_metadata/mdimporter?language=objc) are supported as well as the following additional attributes:

- `_kMDItemUserTags` - list of Finder tags
- `kMDItemDownloadedDate` - list of datetime objects for when the file was downloaded

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

## Finder Info

The Finder keeps some legacy Finder info data about files in a bitstring stored in the `com.apple.FinderInfo` extended attribute. osxmetadata provides some attributes for working with this data.

- `stationerypad`: True if the file is a stationery pad (file template) otherwise False; setting this attribute has the same effect as setting the `Stationery pad` checkbox in the Finder's `Get Info` window.
- `findercolor`: The color of the file as an integer; setting this attribute has the same effect as applying a color label in the Finder's `Get Info` window. osxmetadata will set this attribute automatically when setting user tags; it is recommended you do not set this attribute directly.
- `finderinfo`: The raw Finder info data as a bytes object; you should only manipulate this attribute if you know what you are doing.

## Temporary Files

Spotlight does not appear to index temporary files (those in `/tmp` or `/private/var/tmp`). Setting metadata using osxmetadata on temporary files in these locations will not fail but but it appears the metadata will not be indexed and a subsequent read will return the default value as if the metadata had not been written. This is not a limitation of osxmetadata but rather a limitation of Spotlight. If you need to set metadata on temporary files, you should use a different location.

## Command Line Usage

Installs command line tool called `osxmetadata` which provides a simple interface to view/edit metadata supported by osxmetadata.

If you only care about the command line tool, I recommend installing with [pipx](https://github.com/pipxproject/pipx)

The command line tool can also be run via `python -m osxmetadata`.  Running it with no arguments or with --help option will print a help message:

<!-- [[[cog
import cog
from osxmetadata.__main__ import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli, ["--help"])
help = result.output.replace("Usage: cli", "Usage: osxmetadata")
cog.out(
    "```\n{}\n```".format(help)
)
]]] -->
```
Usage: osxmetadata [OPTIONS] FILE

  Read/write metadata from file(s).

Options:
  -v, --version                   Show the version and exit.
  -w, --walk                      Walk directory tree, processing each file in
                                  the tree.
  -j, --json                      Print output in JSON format, for use with
                                  --list and --get.
  -X, --wipe                      Wipe all metadata attributes from FILE.
  -s, --set ATTRIBUTE VALUE       Set ATTRIBUTE to VALUE. If ATTRIBUTE is a
                                  multi-value attribute, such as keywords
                                  (kMDItemKeywords), you may specify --set
                                  multiple times to add to the array of values:
                                  '--set keywords foo --set keywords bar' will
                                  set keywords to ['foo', 'bar']. Not that this
                                  will overwrite any existing values for the
                                  attribute; see also --append.
  -l, --list                      List all metadata attributes for FILE.
  -c, --clear ATTRIBUTE           Remove attribute from FILE.
  -a, --append ATTRIBUTE VALUE    Append VALUE to ATTRIBUTE; for multi-valued
                                  attributes, appends only if VALUE is not
                                  already present. May be used in combination
                                  with --set to add to an existing value: '--set
                                  keywords foo --append keywords bar' will set
                                  keywords to ['foo', 'bar'], overwriting any
                                  existing values for the attribute.
  -g, --get ATTRIBUTE             Get value of ATTRIBUTE.
  -r, --remove ATTRIBUTE VALUE    Remove VALUE from ATTRIBUTE; only applies to
                                  multi-valued attributes.
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
                                  folder as FILE. Only backs up attributes known
                                  to osxmetadata unless used with --all.
  -R, --restore                   Restore FILE attributes from backup file.
                                  Restore will look for backup file
                                  '.osxmetadata.json' in same folder as FILE.
                                  Only restores attributes known to osxmetadata
                                  unless used with --all.
  -V, --verbose                   Print verbose output.
  -f, --copyfrom SOURCE_FILE      Copy attributes from file SOURCE_FILE (only
                                  updates destination attributes that are not
                                  null in SOURCE_FILE).
  --files-only                    Do not apply metadata commands to directories
                                  themselves, only files in a directory.
  -p, --pattern PATTERN           Only process files matching PATTERN; only
                                  applies to --walk. If specified, only files
                                  matching PATTERN will be processed as each
                                  directory is walked. May be used for than once
                                  to specify multiple patterns. For example, tag
                                  all *.pdf files in projectdir and subfolders
                                  with tag 'project': osxmetadata --append tags
                                  'project' --walk projectdir/ --pattern '*.pdf'
  --help                          Show this message and exit.

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
command line: restore, wipe, copyfrom, clear, set, append, remove, mirror, get,
list, backup.  --backup and --restore are mutually exclusive.  Other options may
be combined or chained together.

Finder tags (tags attribute) contain both a name and an optional color. To
specify the color, append comma + color name (e.g. 'red') after the tag name.
For example --set tags Foo,red. Valid color names are: gray, green, purple,
blue, yellow, red, orange. If color is not specified but a tag of the same name
has already been assigned a color in the Finder, the same color will
automatically be assigned.

com.apple.FinderInfo (finderinfo) value is a key:value dictionary. To set
finderinfo, pass value in format key1:value1,key2:value2,etc. For example:
'osxmetadata --set finderinfo color:2 file.ext'.

Short Name                 Description
acquisitionmake            kMDItemAcquisitionMake;
                           com.apple.metadata:kMDItemAcquisitionMake; The
                           manufacturer of the device used to aquire the
                           document contents.; string
acquisitionmodel           kMDItemAcquisitionModel;
                           com.apple.metadata:kMDItemAcquisitionModel; The
                           model of the device used to aquire the document
                           contents. For example, 100, 200, 400, etc.; string
album                      kMDItemAlbum; com.apple.metadata:kMDItemAlbum; The
                           title for a collection of media. This is analagous
                           to a record album, or photo album.; string
altitude                   kMDItemAltitude;
                           com.apple.metadata:kMDItemAltitude; The altitude of
                           the item in meters above sea level, expressed using
                           the WGS84 datum. Negative values lie below sea
                           level.; string
aperture                   kMDItemAperture;
                           com.apple.metadata:kMDItemAperture; The aperture
                           setting used to acquire the document contents. This
                           unit is the APEX value.; number
appleloopdescriptors       kMDItemAppleLoopDescriptors;
                           com.apple.metadata:kMDItemAppleLoopDescriptors;
                           Specifies multiple pieces of descriptive
                           information about a loop.; list of strings
appleloopskeyfiltertype    kMDItemAppleLoopsKeyFilterType;
                           com.apple.metadata:kMDItemAppleLoopsKeyFilterType;
                           Specifies key filtering information about a loop.
                           Loops are matched against projects that often in a
                           major or minor key.; string
appleloopsloopmode         kMDItemAppleLoopsLoopMode;
                           com.apple.metadata:kMDItemAppleLoopsLoopMode;
                           Specifies how a file should be played.; string
appleloopsrootkey          kMDItemAppleLoopsRootKey;
                           com.apple.metadata:kMDItemAppleLoopsRootKey;
                           Specifies the loop's original key. The key is the
                           root note or tonic for the loop, and does not
                           include the scale type.; string
attributechangedate        kMDItemAttributeChangeDate;
                           com.apple.metadata:kMDItemAttributeChangeDate; The
                           date and time of the last change made to a metadata
                           attribute.; date/time
audiences                  kMDItemAudiences;
                           com.apple.metadata:kMDItemAudiences; The audience
                           for which the file is intended. The audience may be
                           determined by the creator or the publisher or by a
                           third party.; list of strings
audiobitrate               kMDItemAudioBitRate;
                           com.apple.metadata:kMDItemAudioBitRate; The audio
                           bit rate.; number
audiochannelcount          kMDItemAudioChannelCount;
                           com.apple.metadata:kMDItemAudioChannelCount; Number
                           of channels in the audio data contained in the
                           file.; number
audioencodingapplication   kMDItemAudioEncodingApplication;
                           com.apple.metadata:kMDItemAudioEncodingApplication;
                           The name of the application that encoded the data
                           contained in the audio file.; string
audiosamplerate            kMDItemAudioSampleRate;
                           com.apple.metadata:kMDItemAudioSampleRate; Sample
                           rate of the audio data contained in the file. The
                           sample rate is a float value representing hz
                           (audio_frames/second). For example: 44100. 0,
                           22254. 54.; number
audiotracknumber           kMDItemAudioTrackNumber;
                           com.apple.metadata:kMDItemAudioTrackNumber; The
                           track number of a song or composition when it is
                           part of an album.; number
authoraddresses            kMDItemAuthorAddresses;
                           com.apple.metadata:kMDItemAuthorAddresses; This
                           attribute indicates the author addresses of the
                           document.; list of strings
authoremailaddresses       kMDItemAuthorEmailAddresses;
                           com.apple.metadata:kMDItemAuthorEmailAddresses;
                           This attribute indicates the author of the emails
                           message addresses. (This is always the email
                           address, and not the human readable version).; list
                           of strings
authors                    kMDItemAuthors; com.apple.metadata:kMDItemAuthors;
                           The author, or authors, of the contents of the
                           file.; list of strings
bitspersample              kMDItemBitsPerSample;
                           com.apple.metadata:kMDItemBitsPerSample; The number
                           of bits per sample. For example, the bit depth of
                           an image (8-bit, 16-bit etc. . . ) or the bit depth
                           per audio sample of uncompressed audio data (8, 16,
                           24, 32, 64, etc. . ).; number
cfbundleidentifier         kMDItemCFBundleIdentifier;
                           com.apple.metadata:kMDItemCFBundleIdentifier; If
                           this item is a bundle, then this is the
                           CFBundleIdentifier.; string
city                       kMDItemCity; com.apple.metadata:kMDItemCity;
                           Identifies city of origin according to guidelines
                           established by the provider.; string
codecs                     kMDItemCodecs; com.apple.metadata:kMDItemCodecs;
                           The codecs used to encode/decode the media.; list
                           of strings
colorspace                 kMDItemColorSpace;
                           com.apple.metadata:kMDItemColorSpace; The color
                           space model used by the document contents. For
                           example, "RGB", "CMYK", "YUV", or "YCbCr".; string
comment                    kMDItemComment; com.apple.metadata:kMDItemComment;
                           A comment related to the file. This differs from
                           the Finder comment, kMDItemFinderComment.; string
composer                   kMDItemComposer;
                           com.apple.metadata:kMDItemComposer; The composer of
                           the music contained in the audio file.; string
contactkeywords            kMDItemContactKeywords;
                           com.apple.metadata:kMDItemContactKeywords; A list
                           of contacts that are associated with this document,
                           not including the authors.; list of strings
contentcreationdate        kMDItemContentCreationDate;
                           com.apple.metadata:kMDItemContentCreationDate; The
                           creation date of an edited or optimized version of
                           the song or composition.; date/time
contentmodificationdate    kMDItemContentModificationDate;
                           com.apple.metadata:kMDItemContentModificationDate;
                           The date and time that the contents of the file
                           were last modified.; date/time
contenttype                kMDItemContentType;
                           com.apple.metadata:kMDItemContentType; The UTI
                           pedigree of a file.; string
contributors               kMDItemContributors;
                           com.apple.metadata:kMDItemContributors; The
                           entities responsible for making contributions to
                           the content of the resource.; list of strings
copyright                  kMDItemCopyright;
                           com.apple.metadata:kMDItemCopyright; The copyright
                           owner of the file contents.; string
country                    kMDItemCountry; com.apple.metadata:kMDItemCountry;
                           The full, publishable name of the country or region
                           where the intellectual property of the item was
                           created, according to guidelines of the provider.;
                           string
coverage                   kMDItemCoverage;
                           com.apple.metadata:kMDItemCoverage; The extent or
                           scope of the content of the resource.; string
creator                    kMDItemCreator; com.apple.metadata:kMDItemCreator;
                           Application used to create the document content
                           (for example "Word", "Pages", and so on).; string
deliverytype               kMDItemDeliveryType;
                           com.apple.metadata:kMDItemDeliveryType; The
                           delivery type. Values are "Fast start" or "RTSP".;
                           string
description                kMDItemDescription;
                           com.apple.metadata:kMDItemDescription; A
                           description of the content of the resource. The
                           description may include an abstract, table of
                           contents, reference to a graphical representation
                           of content or a free-text account of the content.;
                           string
director                   kMDItemDirector;
                           com.apple.metadata:kMDItemDirector; Directory of
                           the movie.; string
displayname                kMDItemDisplayName;
                           com.apple.metadata:kMDItemDisplayName; The
                           localized version of the file name.; string
downloadeddate             kMDItemDownloadedDate;
                           com.apple.metadata:kMDItemDownloadedDate; Date the
                           item was downloaded.; list of date/time
duedate                    kMDItemDueDate; com.apple.metadata:kMDItemDueDate;
                           Date this item is due.; date/time
durationseconds            kMDItemDurationSeconds;
                           com.apple.metadata:kMDItemDurationSeconds; The
                           duration, in seconds, of the content of file. A
                           value of 10. 5 represents media that is 10 and 1/2
                           seconds long.; number
exifgpsversion             kMDItemEXIFGPSVersion;
                           com.apple.metadata:kMDItemEXIFGPSVersion; The
                           version of GPSInfoIFD in EXIF used to generate the
                           metadata.; string
exifversion                kMDItemEXIFVersion;
                           com.apple.metadata:kMDItemEXIFVersion; The version
                           of the EXIF header used to generate the metadata.;
                           string
emailaddresses             kMDItemEmailAddresses;
                           com.apple.metadata:kMDItemEmailAddresses; Email
                           addresses related to this item.; list of strings
encodingapplications       kMDItemEncodingApplications;
                           com.apple.metadata:kMDItemEncodingApplications;
                           Application used to convert the original content
                           into it's current form. For example, a PDF file
                           might have an encoding application set to
                           "Distiller".; list of strings
exposuremode               kMDItemExposureMode;
                           com.apple.metadata:kMDItemExposureMode; The
                           exposure mode used to acquire the document
                           contents.; number
exposureprogram            kMDItemExposureProgram;
                           com.apple.metadata:kMDItemExposureProgram; The
                           class of the exposure program used by the camera to
                           set exposure when the image is taken. Possible
                           values include: Manual, Normal, and Aperture
                           priority.; string
exposuretimeseconds        kMDItemExposureTimeSeconds;
                           com.apple.metadata:kMDItemExposureTimeSeconds; The
                           exposure time, in seconds, used to acquire the
                           document contents.; number
exposuretimestring         kMDItemExposureTimeString;
                           com.apple.metadata:kMDItemExposureTimeString; The
                           time of the exposure.; string
fnumber                    kMDItemFNumber; com.apple.metadata:kMDItemFNumber;
                           The diameter of the diaphragm aperture in terms of
                           the effective focal length of the lens.; number
fscontentchangedate        kMDItemFSContentChangeDate;
                           com.apple.metadata:kMDItemFSContentChangeDate; The
                           date the file contents last changed.; date/time
fscreationdate             kMDItemFSCreationDate;
                           com.apple.metadata:kMDItemFSCreationDate; The date
                           and time that the file was created.; date/time
fshascustomicon            kMDItemFSHasCustomIcon;
                           com.apple.metadata:kMDItemFSHasCustomIcon; Boolean
                           indicating if this file has a custom icon.; boolean
fsinvisible                kMDItemFSInvisible;
                           com.apple.metadata:kMDItemFSInvisible; Indicates
                           whether the file is invisible.; boolean
fsisextensionhidden        kMDItemFSIsExtensionHidden;
                           com.apple.metadata:kMDItemFSIsExtensionHidden;
                           Indicates whether the file extension of the file is
                           hidden.; boolean
fsisstationery             kMDItemFSIsStationery;
                           com.apple.metadata:kMDItemFSIsStationery; Boolean
                           indicating if this file is stationery.; boolean
fslabel                    kMDItemFSLabel; com.apple.metadata:kMDItemFSLabel;
                           Index of the Finder label of the file. Possible
                           values are 0 through 7.; number
fsname                     kMDItemFSName; com.apple.metadata:kMDItemFSName;
                           The file name of the item.; string
fsnodecount                kMDItemFSNodeCount;
                           com.apple.metadata:kMDItemFSNodeCount; Number of
                           files in a directory.; number
fsownergroupid             kMDItemFSOwnerGroupID;
                           com.apple.metadata:kMDItemFSOwnerGroupID; The group
                           ID of the owner of the file.; number
fsowneruserid              kMDItemFSOwnerUserID;
                           com.apple.metadata:kMDItemFSOwnerUserID; The user
                           ID of the owner of the file.; number
fssize                     kMDItemFSSize; com.apple.metadata:kMDItemFSSize;
                           The size, in bytes, of the file on disk.; number
findercomment              kMDItemFinderComment;
                           com.apple.metadata:kMDItemFinderComment; Finder
                           comments for this file.; string
flashonoff                 kMDItemFlashOnOff;
                           com.apple.metadata:kMDItemFlashOnOff; Indicates if
                           a camera flash was used.; number
focallength                kMDItemFocalLength;
                           com.apple.metadata:kMDItemFocalLength; The actual
                           focal length of the lens, in millimeters.; number
fonts                      kMDItemFonts; com.apple.metadata:kMDItemFonts;
                           Fonts used in this item. You should store the
                           font's full name, the postscript name, or the font
                           family name, based on the available information.;
                           list of strings
gpstrack                   kMDItemGPSTrack;
                           com.apple.metadata:kMDItemGPSTrack; The direction
                           of travel of the item, in degrees from true north.;
                           string
genre                      kMDItemGenre; com.apple.metadata:kMDItemGenre;
                           Genre of the movie.; string
hasalphachannel            kMDItemHasAlphaChannel;
                           com.apple.metadata:kMDItemHasAlphaChannel;
                           Indicates if this image file has an alpha channel.;
                           boolean
headline                   kMDItemHeadline;
                           com.apple.metadata:kMDItemHeadline; A publishable
                           entry providing a synopsis of the contents of the
                           file. For example, "Apple Introduces the iPod
                           Photo".; string
isospeed                   kMDItemISOSpeed;
                           com.apple.metadata:kMDItemISOSpeed; The ISO speed
                           used to acquire the document contents.; number
identifier                 kMDItemIdentifier;
                           com.apple.metadata:kMDItemIdentifier; A formal
                           identifier used to reference the resource within a
                           given context.; string
imagedirection             kMDItemImageDirection;
                           com.apple.metadata:kMDItemImageDirection; The
                           direction of the item's image, in degrees from true
                           north.; string
information                kMDItemInformation;
                           com.apple.metadata:kMDItemInformation; Information
                           about the item.; string
instantmessageaddresses    kMDItemInstantMessageAddresses;
                           com.apple.metadata:kMDItemInstantMessageAddresses;
                           Instant message addresses related to this item.;
                           list of strings
instructions               kMDItemInstructions;
                           com.apple.metadata:kMDItemInstructions; Editorial
                           instructions concerning the use of the item, such
                           as embargoes and warnings. For example, "Second of
                           four stories".; string
isgeneralmidisequence      kMDItemIsGeneralMIDISequence;
                           com.apple.metadata:kMDItemIsGeneralMIDISequence;
                           Indicates whether the MIDI sequence contained in
                           the file is setup for use with a General MIDI
                           device.; boolean
keysignature               kMDItemKeySignature;
                           com.apple.metadata:kMDItemKeySignature; The key of
                           the music contained in the audio file. For example:
                           C, Dm, F#m, Bb.; string
keywords                   kMDItemKeywords;
                           com.apple.metadata:kMDItemKeywords; Keywords
                           associated with this file. For example, "Birthday",
                           "Important", etc.; list of strings
kind                       kMDItemKind; com.apple.metadata:kMDItemKind; A
                           description of the kind of item this file
                           represents.; string
languages                  kMDItemLanguages;
                           com.apple.metadata:kMDItemLanguages; Indicates the
                           languages of the intellectual content of the
                           resource. Recommended best practice for the values
                           of the Language element is defined by RFC 3066.;
                           list of strings
lastuseddate               kMDItemLastUsedDate;
                           com.apple.metadata:kMDItemLastUsedDate; The date
                           and time that the file was last used. This value is
                           updated automatically by LaunchServices everytime a
                           file is opened by double clicking, or by asking
                           LaunchServices to open a file.; date/time
latitude                   kMDItemLatitude;
                           com.apple.metadata:kMDItemLatitude; The latitude of
                           the item in degrees north of the equator, expressed
                           using the WGS84 datum. Negative values lie south of
                           the equator.; string
layernames                 kMDItemLayerNames;
                           com.apple.metadata:kMDItemLayerNames; The names of
                           the layers in the file.; list of strings
longitude                  kMDItemLongitude;
                           com.apple.metadata:kMDItemLongitude; The longitude
                           of the item in degrees east of the prime meridian,
                           expressed using the WGS84 datum. Negative values
                           lie west of the prime meridian.; string
lyricist                   kMDItemLyricist;
                           com.apple.metadata:kMDItemLyricist; The lyricist,
                           or text writer, of the music contained in the audio
                           file.; string
maxaperture                kMDItemMaxAperture;
                           com.apple.metadata:kMDItemMaxAperture; The smallest
                           f-number of the lens. Ordinarily it is given in the
                           range of 00. 00 to 99. 99.; number
mediatypes                 kMDItemMediaTypes;
                           com.apple.metadata:kMDItemMediaTypes; The media
                           types present in the content.; list of strings
meteringmode               kMDItemMeteringMode;
                           com.apple.metadata:kMDItemMeteringMode; The
                           metering mode used to take the image.; string
musicalgenre               kMDItemMusicalGenre;
                           com.apple.metadata:kMDItemMusicalGenre; The musical
                           genre of the song or composition contained in the
                           audio file. For example: Jazz, Pop, Rock,
                           Classical.; string
musicalinstrumentcategory  kMDItemMusicalInstrumentCategory; com.apple.metadat
                           a:kMDItemMusicalInstrumentCategory; Specifies the
                           category of an instrument.; string
musicalinstrumentname      kMDItemMusicalInstrumentName;
                           com.apple.metadata:kMDItemMusicalInstrumentName;
                           Specifies the name of instrument relative to the
                           instrument category.; string
namedlocation              kMDItemNamedLocation;
                           com.apple.metadata:kMDItemNamedLocation; The name
                           of the location or point of interest associated
                           with the item. The name may be user provided.;
                           string
numberofpages              kMDItemNumberOfPages;
                           com.apple.metadata:kMDItemNumberOfPages; Number of
                           pages in the document.; number
organizations              kMDItemOrganizations;
                           com.apple.metadata:kMDItemOrganizations; The
                           company or organization that created the document.;
                           list of strings
orientation                kMDItemOrientation;
                           com.apple.metadata:kMDItemOrientation; The
                           orientation of the document contents. Possible
                           values are 0 (landscape) and 1 (portrait).; number
originalformat             kMDItemOriginalFormat;
                           com.apple.metadata:kMDItemOriginalFormat; Original
                           format of the movie.; string
originalsource             kMDItemOriginalSource;
                           com.apple.metadata:kMDItemOriginalSource; Original
                           source of the movie.; string
pageheight                 kMDItemPageHeight;
                           com.apple.metadata:kMDItemPageHeight; Height of the
                           document page, in points (72 points per inch). For
                           PDF files this indicates the height of the first
                           page only.; number
pagewidth                  kMDItemPageWidth;
                           com.apple.metadata:kMDItemPageWidth; Width of the
                           document page, in points (72 points per inch). For
                           PDF files this indicates the width of the first
                           page only.; number
participants               kMDItemParticipants;
                           com.apple.metadata:kMDItemParticipants; The list of
                           people who are visible in an image or movie or
                           written about in a document.; list of strings
path                       kMDItemPath; com.apple.metadata:kMDItemPath; The
                           complete path to the file.; string
performers                 kMDItemPerformers;
                           com.apple.metadata:kMDItemPerformers; Performers in
                           the movie.; list of strings
phonenumbers               kMDItemPhoneNumbers;
                           com.apple.metadata:kMDItemPhoneNumbers; Phone
                           numbers related to this item.; list of strings
pixelcount                 kMDItemPixelCount;
                           com.apple.metadata:kMDItemPixelCount; The total
                           number of pixels in the contents. Same as
                           kMDItemPixelWidth x kMDItemPixelHeight.; number
pixelheight                kMDItemPixelHeight;
                           com.apple.metadata:kMDItemPixelHeight; The height,
                           in pixels, of the contents. For example, the image
                           height or the video frame height.; number
pixelwidth                 kMDItemPixelWidth;
                           com.apple.metadata:kMDItemPixelWidth; The width, in
                           pixels, of the contents. For example, the image
                           width or the video frame width.; number
producer                   kMDItemProducer;
                           com.apple.metadata:kMDItemProducer; Producer of the
                           content.; string
profilename                kMDItemProfileName;
                           com.apple.metadata:kMDItemProfileName; The name of
                           the color profile used by the document contents.;
                           string
projects                   kMDItemProjects;
                           com.apple.metadata:kMDItemProjects; The list of
                           projects that this file is part of. For example, if
                           you were working on a movie all of the files could
                           be marked as belonging to the project "My Movie".;
                           list of strings
publishers                 kMDItemPublishers;
                           com.apple.metadata:kMDItemPublishers; The entity
                           responsible for making the resource available. For
                           example, a person, an organization, or a service.
                           Typically, the name of a publisher should be used
                           to indicate the entity.; list of strings
recipientaddresses         kMDItemRecipientAddresses;
                           com.apple.metadata:kMDItemRecipientAddresses; This
                           attribute indicates the recipient addresses of the
                           document.; list of strings
recipientemailaddresses    kMDItemRecipientEmailAddresses;
                           com.apple.metadata:kMDItemRecipientEmailAddresses;
                           This attribute indicates the recipients email
                           addresses. (This is always the email address, and
                           not the human readable version).; list of strings
recipients                 kMDItemRecipients;
                           com.apple.metadata:kMDItemRecipients; Recipients of
                           this item.; list of strings
recordingdate              kMDItemRecordingDate;
                           com.apple.metadata:kMDItemRecordingDate; The
                           recording date of the song or composition.;
                           date/time
recordingyear              kMDItemRecordingYear;
                           com.apple.metadata:kMDItemRecordingYear; Indicates
                           the year the item was recorded. For example, 1964,
                           2003, etc.; number
redeyeonoff                kMDItemRedEyeOnOff;
                           com.apple.metadata:kMDItemRedEyeOnOff; Indicates if
                           red-eye reduction was used to take the picture.;
                           boolean
resolutionheightdpi        kMDItemResolutionHeightDPI;
                           com.apple.metadata:kMDItemResolutionHeightDPI;
                           Resolution height, in DPI, of this image.; number
resolutionwidthdpi         kMDItemResolutionWidthDPI;
                           com.apple.metadata:kMDItemResolutionWidthDPI;
                           Resolution width, in DPI, of this image.; number
rights                     kMDItemRights; com.apple.metadata:kMDItemRights;
                           Provides a link to information about rights held in
                           and over the resource.; string
securitymethod             kMDItemSecurityMethod;
                           com.apple.metadata:kMDItemSecurityMethod; The
                           security or encryption method used for the file.;
                           string
speed                      kMDItemSpeed; com.apple.metadata:kMDItemSpeed; The
                           speed of the item, in kilometers per hour.; string
starrating                 kMDItemStarRating;
                           com.apple.metadata:kMDItemStarRating; User rating
                           of this item. For example, the stars rating of an
                           iTunes track.; number
stateorprovince            kMDItemStateOrProvince;
                           com.apple.metadata:kMDItemStateOrProvince;
                           Identifies the province or state of origin
                           according to guidelines established by the
                           provider. For example, "CA", "Ontario", or
                           "Sussex".; string
streamable                 kMDItemStreamable;
                           com.apple.metadata:kMDItemStreamable; Whether the
                           content is prepared for streaming.; boolean
subject                    kMDItemSubject; com.apple.metadata:kMDItemSubject;
                           Subject of the this item.; string
tempo                      kMDItemTempo; com.apple.metadata:kMDItemTempo; A
                           float value that specifies the beats per minute of
                           the music contained in the audio file.; number
textcontent                kMDItemTextContent;
                           com.apple.metadata:kMDItemTextContent; Contains a
                           text representation of the content of the document.
                           Data in multiple fields should be combined using a
                           whitespace character as a separator.; string
theme                      kMDItemTheme; com.apple.metadata:kMDItemTheme;
                           Theme of the this item.; string
timesignature              kMDItemTimeSignature;
                           com.apple.metadata:kMDItemTimeSignature; The time
                           signature of the musical composition contained in
                           the audio/MIDI file. For example: "4/4", "7/8".;
                           string
timestamp                  kMDItemTimestamp;
                           com.apple.metadata:kMDItemTimestamp; The timestamp
                           on the item. This generally is used to indicate the
                           time at which the event captured by the item took
                           place.; string
title                      kMDItemTitle; com.apple.metadata:kMDItemTitle; The
                           title of the file. For example, this could be the
                           title of a document, the name of a song, or the
                           subject of an email message.; string
totalbitrate               kMDItemTotalBitRate;
                           com.apple.metadata:kMDItemTotalBitRate; The total
                           bit rate, audio and video combined, of the media.;
                           number
url                        kMDItemURL; com.apple.metadata:kMDItemURL; Url of
                           the item.; string
version                    kMDItemVersion; com.apple.metadata:kMDItemVersion;
                           The version number of this file.; string
videobitrate               kMDItemVideoBitRate;
                           com.apple.metadata:kMDItemVideoBitRate; The video
                           bit rate.; number
wherefroms                 kMDItemWhereFroms;
                           com.apple.metadata:kMDItemWhereFroms; Describes
                           where the file was obtained from.; list of strings
whitebalance               kMDItemWhiteBalance;
                           com.apple.metadata:kMDItemWhiteBalance; The white
                           balance setting used to acquire the document
                           contents. Possible values are 0 (auto white
                           balance) and 1 (manual).; number


```
<!-- [[[end]]] -->

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
  <tbody>
    <tr>
      <td align="center"><a href="http://www.borja.glezseoane.es"><img src="https://avatars.githubusercontent.com/u/24481419?v=4?s=75" width="75px;" alt="Borja González Seoane"/><br /><sub><b>Borja González Seoane</b></sub></a><br /><a href="https://github.com/RhetTbull/osxmetadata/commits?author=bglezseoane" title="Code">💻</a></td>
      <td align="center"><a href="https://github.com/porg"><img src="https://avatars.githubusercontent.com/u/737143?v=4?s=75" width="75px;" alt="porg"/><br /><sub><b>porg</b></sub></a><br /><a href="https://github.com/RhetTbull/osxmetadata/issues?q=author%3Aporg" title="Bug reports">🐛</a> <a href="#ideas-porg" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center"><a href="https://github.com/nk9"><img src="https://avatars.githubusercontent.com/u/3646730?v=4?s=75" width="75px;" alt="Nick Kocharhook"/><br /><sub><b>Nick Kocharhook</b></sub></a><br /><a href="https://github.com/RhetTbull/osxmetadata/issues?q=author%3Ank9" title="Bug reports">🐛</a></td>
      <td align="center"><a href="https://jakewilliami.github.io/"><img src="https://avatars.githubusercontent.com/u/54291317?v=4?s=75" width="75px;" alt="Jake Ireland"/><br /><sub><b>Jake Ireland</b></sub></a><br /><a href="#ideas-jakewilliami" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center"><a href="https://github.com/luckman212"><img src="https://avatars.githubusercontent.com/u/1992842?v=4?s=75" width="75px;" alt="Luke Hamburg"/><br /><sub><b>Luke Hamburg</b></sub></a><br /><a href="https://github.com/RhetTbull/osxmetadata/issues?q=author%3Aluckman212" title="Bug reports">🐛</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
