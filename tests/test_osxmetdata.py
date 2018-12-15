#!/usr/bin/env python

import unittest
from tempfile import NamedTemporaryFile

from osxmetadata import OSXMetaData

class TestOSXMetaData(unittest.TestCase):
    # TESTDIR for temporary files usually defaults to "/tmp",
    # which may not have XATTR support (e.g. tmpfs);
    # manual override here.
    TESTDIR = None

    def test_tags(self):
    #     # Not using setlocale(LC_ALL, ..) to set locale because
    #     # sys.getfilesystemencoding() implementation falls back
    #     # to user's preferred locale by calling setlocale(LC_ALL, '').
    #     xattr.compat.fs_encoding = 'UTF-8'

        #can we update tags?
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

        #remove tags
        meta.tags.remove('Test')
        self.assertEqual(set(meta.tags),set(['Green','Foo','Bar']))

        #clear tags
        meta.tags.clear()
        self.assertEqual(set(meta.tags),set([]))

    def setUp(self):
        self.tempfile = NamedTemporaryFile(dir=self.TESTDIR)
        self.tempfilename = self.tempfile.name

    def tearDown(self):
        self.tempfile.close()

if __name__ == '__main__':
    unittest.main()

