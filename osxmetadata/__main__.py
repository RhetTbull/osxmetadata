# /usr/bin/env python3

import datetime
import json
import logging
import os
import os.path
import pathlib
import sys

import click

import osxmetadata

from ._version import __version__
from .attributes import _LONG_NAME_WIDTH, _SHORT_NAME_WIDTH, ATTRIBUTES
from .constants import _TAGS_NAMES
from .utils import validate_attribute_value

# TODO: add md5 option
# TODO: how is metadata on symlink handled?
# should symlink be resolved before gathering metadata?
# currently, symlinks are resolved before handling metadata but not sure this is the right behavior
# in 10.13.6: synlinks appear to inherit tags but not Finder Comments:
#   e.g. changes to tags in a file changes tags in the symlink but symlink can have it's own finder comment
#   Finder aliases inherit neither
# TODO: add selective restore (e.g only restore files matching command line path)
#   e.g osxmetadata -r meta.json *.pdf

# TODO: need special handling for --set color GREEN, etc.


# Click CLI object & context settings
class CLI_Obj:
    def __init__(self, debug=False, files=None):
        self.debug = debug
        if debug:
            osxmetadata._set_debug(True)

        self.files = files


class MyClickCommand(click.Command):
    """ Custom click.Command that overrides get_help() to show additional info """

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()

        # build help text from all the attribute names
        # get set of attribute names
        # (to eliminate the duplicate entries for short_constant and long costant)
        # then sort and get the short constant, long constant, and help text
        # passed to click.HelpFormatter.write_dl for formatting
        attr_tuples = [("Short Name", "Description")]
        attr_tuples.extend(
            (
                ATTRIBUTES[attr].name,
                f"{ATTRIBUTES[attr].short_constant}, "
                + f"{ATTRIBUTES[attr].constant}; {ATTRIBUTES[attr].help}",
            )
            for attr in sorted(
                [attr for attr in {attr.name for attr in ATTRIBUTES.values()}]
            )
        )

        formatter.write("\n\n")
        formatter.write_text(
            "Valid attributes for ATTRIBUTE: "
            + "Each attribute has a short name, a constant name, and a long constant name. "
            + "Any of these may be used for ATTRIBUTE"
        )
        formatter.write("\n")
        formatter.write_text('For example: --set findercomment "Hello world"')
        formatter.write_text('or:          --set kMDFinderComment "Hello world"')
        formatter.write_text(
            'or:          --set com.apple.metadata:kMDItemFinderComment "Hello world"'
        )
        formatter.write("\n")
        formatter.write_text(
            "Attributes that are strings can only take one value for --set; "
            + "--append will append to the existing value.  "
            + "Attributes that are arrays can be set multiple times to add to the array: "
            + "e.g. --set keywords 'foo' --set keywords 'bar' will set keywords to ['foo', 'bar']"
        )
        formatter.write("\n")

        formatter.write_dl(attr_tuples)
        help_text += formatter.getvalue()
        return help_text


CTX_SETTINGS = dict(help_option_names=["--help", "-h"])
FILES_ARGUMENT = click.argument(
    "files", metavar="FILE", nargs=-1, type=click.Path(exists=True)
)
WALK_OPTION = click.option(
    "--walk",
    "-w",
    is_flag=True,
    help="Walk directory tree, processing each file in the tree",
    default=False,
)
JSON_OPTION = click.option(
    "--json",
    "-j",
    "json_",
    is_flag=True,
    help="Print output in JSON format, for use with --list.",
    default=False,
    hidden=True,
)
DEBUG_OPTION = click.option(
    "--debug", required=False, is_flag=True, default=False, hidden=True
)
SET_OPTION = click.option(
    "--set",
    "set_",
    metavar="ATTRIBUTE VALUE",
    help="Set ATTRIBUTE to VALUE",
    nargs=2,
    multiple=True,
    required=False,
)
GET_OPTION = click.option(
    "--get",
    help="Get value of ATTRIBUTE",
    metavar="ATTRIBUTE",
    nargs=1,
    multiple=True,
    required=False,
)
LIST_OPTION = click.option(
    "--list",
    "list_",
    help="List all metadata attributes for FILE",
    is_flag=True,
    default=False,
)
CLEAROPTION = click.option(
    "--clear",
    help="Remove attribute from FILE",
    metavar="ATTRIBUTE",
    nargs=1,
    multiple=True,
    required=False,
)
APPEND_OPTION = click.option(
    "--append",
    metavar="ATTRIBUTE VALUE",
    help="Append VALUE to ATTRIBUTE",
    nargs=2,
    multiple=True,
    required=False,
)
UPDATE_OPTION = click.option(
    "--update",
    metavar="ATTRIBUTE VALUE",
    help="Update ATTRIBUTE with VALUE; for multi-valued attributes, "
    "this adds VALUE to the attribute if not already in the list",
    nargs=2,
    multiple=True,
    required=False,
)
REMOVE_OPTION = click.option(
    "--remove",
    metavar="ATTRIBUTE VALUE",
    help="Remove VALUE from ATTRIBUTE; only applies to multi-valued attributes",
    nargs=2,
    multiple=True,
    required=False,
)


@click.command(cls=MyClickCommand)
@click.version_option(__version__, "--version", "-v")
@DEBUG_OPTION
@FILES_ARGUMENT
@WALK_OPTION
@JSON_OPTION
@SET_OPTION
@LIST_OPTION
@CLEAROPTION
@APPEND_OPTION
@GET_OPTION
@REMOVE_OPTION
@UPDATE_OPTION
@click.pass_context
def cli(
    ctx, debug, files, walk, json_, set_, list_, clear, append, get, remove, update
):
    """ Read/write metadata from file(s). """

    if debug:
        logging.disable(logging.NOTSET)

    logging.debug(
        f"ctx={ctx} debug={debug} files={files} walk={walk} json={json_} "
        f"set={set_}, list={list_},clear={clear},append={append},get={get}, remove={remove}"
    )

    if not files:
        click.echo(ctx.get_help())
        ctx.exit()

    # validate values for --set, --clear, append, get, remove
    if any([set_, append, remove, clear, get]):
        attributes = (
            [a[0] for a in set_] + [a[0] for a in append] + list(clear) + list(get)
        )
        logging.debug(f"attributes = {attributes}")
        invalid_attr = False
        for attr in attributes:
            logging.debug(f"attr = {attr}")
            if attr not in ATTRIBUTES:
                click.echo(f"Invalid attribute {attr}", err=True)
                invalid_attr = True
        if invalid_attr:
            click.echo("")  # add a new line before rest of help text
            click.echo(ctx.get_help())
            ctx.exit()

    for f in files:
        if walk and os.path.isdir(f):
            for root, _, filenames in os.walk(f):
                # if verbose:
                #     print(f"Processing {root}")
                for fname in filenames:
                    fpath = pathlib.Path(f"{root}/{fname}").resolve()
                    process_file(
                        fpath, json_, set_, append, update, remove, clear, get, list_
                    )
        elif os.path.isdir(f):
            # skip directory
            logging.debug(f"skipping directory: {f}")
            continue
        else:
            fpath = pathlib.Path(f).resolve()
            process_file(fpath, json_, set_, append, update, remove, clear, get, list_)


def process_file(fpath, json_, set_, append, update, remove, clear, get, list_):
    """ process a single file to apply the options 
        options processed in this order: set, append, remove, clear, get, list
        Note: expects all attributes passed in parameters to be validated """

    logging.debug(f"process_file: {fpath}")

    md = osxmetadata.OSXMetaData(fpath)

    if set_:
        # set data
        # check attribute is valid
        attr_dict = {}
        for item in set_:
            attr, val = item
            attribute = ATTRIBUTES[attr]
            logging.debug(f"setting {attr}={val}")
            try:
                attr_dict[attribute].append(val)
            except KeyError:
                attr_dict[attribute] = [val]

        for attribute, value in attr_dict.items():
            logging.debug(f"value: {value}")
            value = validate_attribute_value(attribute, value)
            # tags get special handling
            if attribute.name in _TAGS_NAMES:
                tags = md.tags
                tags.clear()
                tags.update(*value)
            else:
                md.set_attribute(attribute.name, value)

    if append:
        # append data
        # check attribute is valid
        attr_dict = {}
        for item in append:
            attr, val = item
            attribute = ATTRIBUTES[attr]
            logging.debug(f"appending {attr}={val}")
            try:
                attr_dict[attribute].append(val)
            except KeyError:
                attr_dict[attribute] = [val]

        for attribute, value in attr_dict.items():
            value = validate_attribute_value(attribute, value)
            # tags get special handling
            if attribute.name in _TAGS_NAMES:
                tags = md.tags
                tags.update(*value)
            else:
                md.append_attribute(attribute.name, value)

    if update:
        # update data
        # check attribute is valid
        attr_dict = {}
        for item in update:
            attr, val = item
            attribute = ATTRIBUTES[attr]
            logging.debug(f"appending {attr}={val}")
            try:
                attr_dict[attribute].append(val)
            except KeyError:
                attr_dict[attribute] = [val]

        for attribute, value in attr_dict.items():
            value = validate_attribute_value(attribute, value)
            # tags get special handling
            if attribute.name in _TAGS_NAMES:
                tags = md.tags
                tags.update(*value)
            else:
                md.update_attribute(attribute.name, value)

    if remove:
        # remove value from attribute
        # actually implemented with discard so no error raised if not present
        # todo: catch errors and display help
        for attr, val in remove:
            try:
                attribute = ATTRIBUTES[attr]
                md.discard_attribute(attribute.name, val)
            except KeyError as e:
                raise e

    if clear:
        for attr in clear:
            attribute = ATTRIBUTES[attr]
            logging.debug(f"clearing {attr}")
            md.clear_attribute(attribute.name)

    if get:
        logging.debug(f"get: {get}")
        for attr in get:
            attribute = ATTRIBUTES[attr]
            logging.debug(f"getting {attr}")
            # tags get special handling
            if attribute.name in _TAGS_NAMES:
                value = md.tags
            else:
                value = md.get_attribute(attribute.name)
            click.echo(
                f"{attribute.name:{_SHORT_NAME_WIDTH}}{attribute.constant:{_LONG_NAME_WIDTH}} = {value}"
            )

    if list_:
        attribute_list = md.list_metadata()
        for attr in attribute_list:
            try:
                attribute = ATTRIBUTES[attr]
                # tags get special handling
                if attribute.name in _TAGS_NAMES:
                    # TODO: need to fix it so tags can be returned with proper formatting by get_attribute
                    value = md.tags
                else:
                    value = md.get_attribute_str(attribute.name)
                click.echo(
                    f"{attribute.name:{_SHORT_NAME_WIDTH}}{attribute.constant:{_LONG_NAME_WIDTH}} = {value}"
                )
            except KeyError:
                click.echo(
                    f"{'UNKNOWN':{_SHORT_NAME_WIDTH}}{attr:{_LONG_NAME_WIDTH}} = THIS ATTRIBUTE NOT HANDLED"
                )


def write_json_data(fp, data):
    json.dump(data, fp)
    fp.write("\n")


# def write_text_data(fp, data):
#     file = data["file"]

#     fc = data["fc"]
#     fc = fc if fc is not None else ""

#     dldate = data["dldate"]
#     dldate = dldate if dldate is not None else ""

#     desc = data["description"]
#     desc = desc if desc is not None else ""

#     where_from = data["where_from"]
#     where_from = where_from if where_from is not None else ""

#     tags = data["tags"]
#     tags = tags if len(tags) != 0 else ""

#     print(f"file: {file}", file=fp)
#     print(f"description: {desc}", file=fp)
#     print(f"tags: {tags}", file=fp)
#     print(f"Finder comment: {fc}", file=fp)
#     print(f"Download date: {dldate}", file=fp)
#     print(f"Where from: {where_from}", file=fp)
#     print("\n", file=fp)


# def restore_from_json(json_file, quiet=False):
#     fp = None
#     try:
#         fp = open(json_file, mode="r")
#     except:
#         print(f"Error opening file {json_file} for reading")
#         sys.exit(2)

#     for line in fp:
#         data = json.loads(line)
#         if not quiet:
#             print(f"Restoring metadata for {data['file']}")
#         set_metadata(data, quiet)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
