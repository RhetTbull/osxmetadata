osxmetadata [Homepage](https://github.com/RhetTbull/osxmetadata)
========

What is osxmetadata?
-----------------

osxmetadata provides a simple interface to access various metadata about Mac OS X files.  Currently supported metadata includes tags/keywords, Finder comments, and download data (downloaded where from and downloaded data).  This module was inspired by [osx-tags](https://github.com/scooby/osx-tags) by "Ben S / scooby" and extended for my needs.  It is published under the same MIT license.

Supported operating systems
---------------------------

Only works on Mac OS X.

Installation instructions
-------------------------

osxmetadata uses setuptools, thus simply run:

	python setup.py install

Command Line Usage
------------------

Installs command line tool called osxmetadata.  This is not full replacement for ```mdls``` and ```xattr``` commands but provides a simple interface to view/edit metadata supported by osxmetadata

Currently, only supports reading/writing tags and export to text or JSON.  I will add additional metadata as well as import from JSON in the future.

```
usage: osxmetadata [-h] [-v] [-j] [-q] [--noprogress] [--force] [-o OUTFILE]
                   [--addtag ADDTAG] [--cleartags] [--rmtag RMTAG]
                   [files [files ...]]

Import and export metadata from files

positional arguments:
  files

optional arguments:
  -h, --help            Show this help message
  -v, --verbose         Print verbose output during processing
  -j, --json            Output to JSON, optionally provide output file name:
                        --file=file.json
  -q, --quiet           Be extra quiet when running.
  --noprogress          Disable the progress bar while running
  --force               Force new metadata to be written even if unchanged
  -o OUTFILE, --outfile OUTFILE
                        Name of output file. If not specified, output goes to
                        STDOUT
  --addtag ADDTAG       add tags/keywords for file
  --cleartags           remove all tags from file
  --rmtag RMTAG         remove tag from file
```


Example uses of the module
--------------------------

```python
from osxmetadata import *

fname = 'foo.txt'

meta = OSXMetaData(fname)
print(meta.name)
print(meta.finder_comment)
print(meta.tags)
print(meta.where_from)
print(str(meta.download_date))

```
Tags
----

Accessed via OSXMetaData.tags

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

Finder Comments
---------------

Accessed via OXMetaData.finder_comment

Behaves mostly like a string.  You can assign a string or use +=. To clear, assign None or ''

```python
>>> md.finder_comment = 'My Comment'
>>> print(md.finder_comment)
My Comment
>>> md.finder_comment += ', and FooBar!'
>>> print(md.finder_comment)
My Comment, and FooBar!
>>> md.finder_comment = None
>>> print(md.finder_comment)

>>>
```

Download Data
-------------
Accessed via OSXMetaData.download_date (datetime.datetime object) and OSXMetaData.where_from (list of URLs as strings)


```python
>>> import datetime
>>> md.download_date = datetime.datetime.now()
>>> print(str(md.download_date))
2018-12-15 15:45:10.869535
>>> md.where_from = ['http://wwww.mywebsite.com','https://downloads.mywebsite.com/downloads/foo']
>>> print(md.where_from)
['http://wwww.mywebsite.com', 'https://downloads.mywebsite.com/downloads/foo']
>>> md.where_from=[]
>>> print(md.where_from)
[]
>>>
```

Usage Notes
-----------
Changes are immediately written to the file.  For example, OSXMetaData.tags.add('Foo') immediately writes the tag 'Foo' to the file.

Metadata is refreshed from disk every time a class property is accessed.

This will only work on file systems that support Mac OS X extended attributes.

Dependencies
------------
[PyObjC](https://pythonhosted.org/pyobjc/)

[xattr](https://github.com/xattr/xattr)

Acknowledgements
----------------
This module was inspired by [osx-tags]( https://github.com/scooby/osx-tags) by "Ben S / scooby".  I leveraged osx-tags to bootstrap the design of this module.  I wanted a more
general OS X metadata library so I rolled my own.

To set the Finder comments, I use [py-applescript]( https://github.com/rdhyee/py-applescript) by "Raymond Yee / rdhyee".  Rather than import this module, I included the entire module
(which is published as public domain code) in a private module to prevent ambiguity with
other applescript modules on PyPi.  py-applescript uses a native bridge via PyObjC and
is very fast compared to the other osascript based modules.
