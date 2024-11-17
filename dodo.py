"""Task list for doit, used to build the project; run with `doit` or `doit list` to see commands"""

import osxmetadata


def task_update_readme():
    """Update README with CLI output"""
    return {"actions": ["cog -r README.md"]}


# def task_test():
#     """Run tests"""
#     return {"actions": ["pytest --doctest-glob=README.md tests/"]}


def task_docs():
    """Build docs"""
    return {"actions": ["mkdocs build"]}


def task_gh_docs():
    """Build docs and push to gh-pages"""
    return {
        "actions": [
            "mkdocs gh-deploy --force",
        ]
    }


def task_clean_build_files():
    """Clean out old build files"""
    return {
        "actions": ["rm -rf dist/", "rm -rf build/"],
    }


def task_build():
    """Build python project"""
    return {"actions": ["python3 -m build"]}


def task_build_exe():
    """Build exe with pyinstaller"""
    return {
        "actions": [
            'pyinstaller --onefile --hidden-import="pkg_resources.py2_warn" --name osxmetadata '
            "--add-data osxmetadata/attribute_data/audio_attributes.json:osxmetadata/attribute_data "
            "--add-data osxmetadata/attribute_data/common_attributes.json:osxmetadata/attribute_data "
            "--add-data osxmetadata/attribute_data/filesystem_attributes.json:osxmetadata/attribute_data "
            "--add-data osxmetadata/attribute_data/image_attributes.json:osxmetadata/attribute_data "
            "--add-data osxmetadata/attribute_data/mdimporter_constants.json:osxmetadata/attribute_data "
            "--add-data osxmetadata/attribute_data/nsurl_resource_keys.json:osxmetadata/attribute_data "
            "--add-data osxmetadata/attribute_data/video_attributes.json:osxmetadata/attribute_data "
            "cli.py"
        ]
    }


def task_zip_exe():
    """Zip executable for release"""
    version = osxmetadata._version.__version__
    return {
        "actions": [
            f"zip dist/osxmetadata_MacOS_exe_darwin_x64_v{version}.zip dist/osxmetadata",
            "rm dist/osxmetadata",
        ]
    }
