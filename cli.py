""" stand alone command line script for use with pyinstaller
    
    Note: This is *not* the cli that "python3 -m pip install osxmetadata" or "python setup.py install" would install;
    it's merely a wrapper around __main__.py to allow pyinstaller to work

    This script is built with `doit build_exe` and the resulting executable is zipped with `doit zip_exe` 
"""

from osxmetadata.__main__ import cli

if __name__ == "__main__":
    cli()
