#!/usr/bin/env python

import unittest
from tempfile import NamedTemporaryFile
from sys import platform
from pathlib import Path
import datetime

from osxmetadata import OSXMetaData, _MAX_FINDERCOMMENT

class TestOSXMetaData(unittest.TestCase):
    # TESTDIR for temporary files usually defaults to "/tmp",
    # which may not have XATTR support (e.g. tmpfs);
    # manual override here.
    TESTDIR = None

    def test_platform(self):
        #this module only works on Mac (darwin)
        self.assertEqual(platform,'darwin')

    def test_tags(self):
    #     # Not using setlocale(LC_ALL, ..) to set locale because
    #     # sys.getfilesystemencoding() implementation falls back
    #     # to user's preferred locale by calling setlocale(LC_ALL, '').
    #     xattr.compat.fs_encoding = 'UTF-8'

        #update tags
        meta = OSXMetaData(self.tempfilename)
        tagset = ['Test','Green']
        meta.tags.update(*tagset)
        self.assertEqual(set(meta.tags),set(tagset))

        #add tags
        meta.tags.add('Foo')
        self.assertNotEqual(set(meta.tags),set(tagset))
        self.assertEqual(set(meta.tags),set(['Test','Green','Foo']))

        #__iadd__
        meta.tags += 'Bar'
        self.assertEqual(set(meta.tags),set(['Test','Green','Foo','Bar']))

        #__repr__
        tags = set(meta.tags)
        self.assertEqual(tags,set(['Test','Green','Foo','Bar']))

        #remove tags
        meta.tags.remove('Test')
        self.assertEqual(set(meta.tags),set(['Green','Foo','Bar']))

        #remove tag that doesn't exist, raises KeyError
        with self.assertRaises(KeyError):
            meta.tags.remove('FooBar')

        #discard tags
        meta.tags.discard('Green')
        self.assertEqual(set(meta.tags),set(['Foo','Bar']))
        
        #discard tag that doesn't exist, no error
        meta.tags.discard('FooBar')
        self.assertEqual(set(meta.tags),set(['Foo','Bar']))

        #len
        num = len(meta.tags)
        self.assertEqual(num,2)

        #clear tags
        meta.tags.clear()
        self.assertEqual(set(meta.tags),set([]))

        
    def test_finder_comments(self):
        meta = OSXMetaData(self.tempfilename)
        fc = 'This is my new comment'
        meta.finder_comment = fc
        self.assertEqual(meta.finder_comment,fc)
        meta.finder_comment += ', foo'
        fc += ', foo'
        self.assertEqual(meta.finder_comment, fc)
        
        with self.assertRaises(ValueError):
            meta.finder_comment = 'x'*_MAX_FINDERCOMMENT + 'x'

        #set finder comment to None same as ''
        meta.finder_comment = None 
        self.assertEqual(meta.finder_comment,'')

        meta.finder_comment = ''
        self.assertEqual(meta.finder_comment,'')

    def test_name(self):
        meta = OSXMetaData(self.tempfilename)
        fname = Path(self.tempfilename)
        self.assertEqual(meta.name,fname.resolve().as_posix())

    def test_download_date(self):
        meta = OSXMetaData(self.tempfilename)
        dt = datetime.datetime.now()
        meta.download_date = dt
        self.assertEqual(meta.download_date, dt)

    def test_download_where_from(self):
        meta = OSXMetaData(self.tempfilename)
        meta.where_from = ['http://google.com','https://apple.com']
        wf = meta.where_from
        self.assertEqual(wf,['http://google.com','https://apple.com'])

    def setUp(self):
        self.tempfile = NamedTemporaryFile(dir=self.TESTDIR)
        self.tempfilename = self.tempfile.name

    def tearDown(self):
        self.tempfile.close()

if __name__ == '__main__':
    unittest.main()

