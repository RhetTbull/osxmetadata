"""Task list for doit, used to build the project; run with `doit` or `doit list` to see commands"""

import osxmetadata


def task_update_readme():
    """Update README with CLI output"""
    return {"actions": ["poetry run cog -r README.md"]}


def task_test():
    """Run tests"""
    return {"actions": ["poetry run pytest --doctest-glob=README.md tests/"]}


def task_docs():
    """Build docs"""
    return {"actions": ["poetry run mkdocs build"]}


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
            'pyinstaller --onefile --hidden-import="pkg_resources.py2_warn" --name osxmetadata cli.py'
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
