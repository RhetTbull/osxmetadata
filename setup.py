#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# setup.py script for osxmetdata
#
# Copyright (c) 2018 Rhet Turnbull, rturnbull+git@gmail.com
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#from distutils.core import setup
from setuptools import setup

setup(
       name         = 'osxmetadata',
       version      = '0.92',
       description  = 'Read and write meta data, such as tags/keywords, on Mac OS X files',
       author       = 'Rhet Turnbull',
       author_email = 'rturnbull+git@gmail.com',
       url          = 'https://github.com/RhetTbull/',
       project_urls = {
                       'GitHub': 'https://github.com/RhetTbull/osxmetadata'
                      },
       download_url = 'https://github.com/RhetTbull/osxmetadata',
       packages = ['osxmetadata'],
       py_modules   = ['osxmetadata'],
       license      = 'License :: OSI Approved :: MIT License',
       classifiers  = [
                       'Development Status :: 4 - Beta',
                       'Environment :: MacOS X'
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: MIT License',
                       'Operating System :: MacOS :: MacOS X',
                       'Programming Language :: Python',
                       'Topic :: Software Development :: Libraries :: Python Modules',
         ]
     )
