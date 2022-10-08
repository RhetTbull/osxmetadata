# Tests for osxphotos

## Running Tests

Tests require pytest which will be installed by poetry.  To run tests, use:

`poetry run pytest --doctest-glob=README.md tests/ README.md -v`

The `--doctest-glob=README.md` option is required to run the doctests in the main README.md file.

## Test Data

The test suite includes some image, audio, and video files in the `tests/` folder.  These files were produced by the author and are licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/). The files are used for testing purposes only and are not included in the osxphotos package.
