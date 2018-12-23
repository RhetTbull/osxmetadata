osxmetadata [Homepage](https://github.com/RhetTbull/osxmetadata)
========

What is osxmetadata?
-----------------

osxmetadata provides a simple interface to access various metadata about Mac OS X files.  Currently supported metadata includes tags/keywords, Finder comments, and download data (downloaded where from and downloaded data).  This module was inspired by [osx-tags]( https://github.com/scooby/osx-tags) by "Ben S / scooby" and extended for my needs.  It is published under the same MIT license.

Supported operating systems
---------------------------

Only works on Mac OS X.

Installation instructions
-------------------------

osxmetadata uses setuptools, thus simply run:

	python setup.py install

Command Line Usage
------------------

Currently no command line tool.  I will likely include a command line tool in a future version.

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
