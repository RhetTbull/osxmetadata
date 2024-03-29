# Developer Notes For osxmetadata

These are notes to help me remember how to build and release osxmetadata. They may be useful for contributors.

## Tooling

The build is managed by [doit](https://pydoit.org/) and [poetry](https://python-poetry.org/).  Version management uses [bump2version](https://github.com/c4urself/bump2version).  Documentation is updated with [cog](https://nedbatchelder.com/code/cog/) and [mkdocs](https://www.mkdocs.org/). [pytest](https://docs.pytest.org/en/stable/) is used for testing.

To bump the minor version, run `bumpversion minor --verbose --dry-run` to see what will happen then again without the `--dru-run` to implement the change. This updates the `__version__` constant in the package as well as the poetry version.

## Setting up the environment

- `pip install poetry`
- `poetry install`
- `poetry shell` to activate the virtual environment

## Testing

The doit `test` task (`doit test`) will run pytest to test the package. (You'll need to have used `poetry shell` before running `doit` to activate the poetry environment.) The README.md file contains some example code that can be tested with `poetry run pytest --doctest-glob=README.md`.  The `test` task will do this automatically.

Note that a couple of tests are currently failing on Ventura even though the same code works fine when run directly. I've not figured out why this is happening yet.

## Building

To test and build the package, run `doit`. This will build the package and run the tests.  Run `doit list` to see the available tasks.  doit tasks are defined in `dodo.py`.

## Docs

Uses `mkdocs`:

- `mkdocs build`
- `mkdocs gh-deploy`

## Changelog

Use [auto-changelog](https://github.com/cookpete/auto-changelog):

- `auto-changelog --ignore-commit-pattern CHANGELOG -l 5`
