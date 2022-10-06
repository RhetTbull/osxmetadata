"""Test osxmetadata path property"""

import os

from osxmetadata import OSXMetaData


def test_asdict(test_file):
    """Test asdict method"""
    md = OSXMetaData(test_file.name)
    cwd = os.getcwd()
    assert md.path == os.path.join(cwd, test_file.name)
