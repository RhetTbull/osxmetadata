#!/bin/sh 

# This will build an stand-alone executable called 'osxmetadata' in your ./dist directory
# using pyinstaller
# If you need to install pyinstaller:
# python3 -m pip install --upgrade pyinstaller

pyinstaller --onefile --hidden-import="pkg_resources.py2_warn" --name osxmetadata cli.py