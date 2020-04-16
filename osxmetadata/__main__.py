# /usr/bin/env python3

import datetime
import itertools
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
from .classes import _AttributeList, _AttributeTagsList
from .constants import _BACKUP_FILENAME, _TAGS_NAMES
from .utils import load_backup_file, write_backup_file

# TODO: how is metadata on symlink handled?
# should symlink be resolved before gathering metadata?
# currently, symlinks are resolved before handling metadata but not sure this is the right behavior
# in 10.13.6: synlinks appear to inherit tags but not Finder Comments:
#   e.g. changes to tags in a file changes tags in the symlink but symlink can have it's own finder comment
#   Finder aliases inherit neither
# TODO: add selective restore (e.g only restore files matching command line path)
#   e.g osxmetadata -r meta.json *.pdf


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
        formatter.write_text('or:          --set kMDItemFinderComment "Hello world"')
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
        formatter.write_text(
            "Options are executed in the following order regardless of order "
            + "passed on the command line: "
            + "restore, wipe, copyfrom, clear, set, append, update, remove, mirror, get, list, backup.  "
            + "--backup and --restore are mutually exclusive.  "
            + "Other options may be combined or chained together."
        )
        formatter.write("\n")

        formatter.write_dl(attr_tuples)
        help_text += formatter.getvalue()
        return help_text


# All the command line options defined here
FILES_ARGUMENT = click.argument(
    "files", metavar="FILE", nargs=-1, type=click.Path(exists=True)
)
HELP_OPTION = click.option(
    # add this only so I can show help text via echo_via_pager
    "--help",
    "-h",
    "help_",
    help="Show this message and exit.",
    is_flag=True,
    default=False,
    required=False,
)
WALK_OPTION = click.option(
    "--walk",
    "-w",
    is_flag=True,
    help="Walk directory tree, processing each file in the tree.",
    default=False,
)
JSON_OPTION = click.option(
    "--json",
    "-j",
    "json_",
    is_flag=True,
    help="Print output in JSON format, for use with --list and --get.",
    default=False,
)
DEBUG_OPTION = click.option(
    "--debug", required=False, is_flag=True, default=False, hidden=True
)
SET_OPTION = click.option(
    "--set",
    "-s",
    "set_",
    metavar="ATTRIBUTE VALUE",
    help="Set ATTRIBUTE to VALUE.",
    nargs=2,
    multiple=True,
    required=False,
)
GET_OPTION = click.option(
    "--get",
    "-g",
    help="Get value of ATTRIBUTE.",
    metavar="ATTRIBUTE",
    nargs=1,
    multiple=True,
    required=False,
)
LIST_OPTION = click.option(
    "--list",
    "-l",
    "list_",
    help="List all metadata attributes for FILE.",
    is_flag=True,
    default=False,
)
CLEAR_OPTION = click.option(
    "--clear",
    "-c",
    help="Remove attribute from FILE.",
    metavar="ATTRIBUTE",
    nargs=1,
    multiple=True,
    required=False,
)
WIPE_OPTION = click.option(
    "--wipe",
    "-X",
    help="Wipe all metadata attributes from FILE.",
    is_flag=True,
    default=False,
    required=False,
)
APPEND_OPTION = click.option(
    "--append",
    "-a",
    metavar="ATTRIBUTE VALUE",
    help="Append VALUE to ATTRIBUTE.",
    nargs=2,
    multiple=True,
    required=False,
)
UPDATE_OPTION = click.option(
    "--update",
    "-u",
    metavar="ATTRIBUTE VALUE",
    help="Update ATTRIBUTE with VALUE; for multi-valued attributes, "
    "this adds VALUE to the attribute if not already in the list.",
    nargs=2,
    multiple=True,
    required=False,
)
REMOVE_OPTION = click.option(
    "--remove",
    "-r",
    metavar="ATTRIBUTE VALUE",
    help="Remove VALUE from ATTRIBUTE; only applies to multi-valued attributes.",
    nargs=2,
    multiple=True,
    required=False,
)
MIRROR_OPTION = click.option(
    "--mirror",
    "-m",
    metavar="ATTRIBUTE1 ATTRIBUTE2",
    help="Mirror values between ATTRIBUTE1 and ATTRIBUTE2 so that ATTRIBUTE1 = ATTRIBUTE2; "
    "for multi-valued attributes, merges values; for string attributes, sets ATTRIBUTE1 = ATTRIBUTE2 "
    "overwriting any value in ATTRIBUTE1.  "
    "For example: '--mirror keywords tags' sets tags and keywords to same values.",
    nargs=2,
    required=False,
    multiple=True,
)
BACKUP_OPTION = click.option(
    "--backup",
    "-B",
    help="Backup FILE attributes.  "
    "Backup file '.osxmetadata.json' will be created in same folder as FILE.",
    is_flag=True,
    required=False,
    default=False,
)
RESTORE_OPTION = click.option(
    "--restore",
    "-R",
    help="Restore FILE attributes from backup file.  "
    "Restore will look for backup file '.osxmetadata.json' in same folder as FILE.",
    is_flag=True,
    required=False,
    default=False,
)
VERBOSE_OPTION = click.option(
    "--verbose",
    "-V",
    help="Print verbose output.",
    is_flag=True,
    default=False,
    required=False,
)
COPY_FROM_OPTION = click.option(
    "--copyfrom",
    "-f",
    metavar="SOURCE_FILE",
    help="Copy attributes from file SOURCE_FILE.",
    type=click.Path(exists=True),
    nargs=1,
    multiple=False,
    required=False,
)


@click.command(cls=MyClickCommand)
@click.version_option(__version__, "--version", "-v")
@HELP_OPTION
@DEBUG_OPTION
@FILES_ARGUMENT
@WALK_OPTION
@JSON_OPTION
@WIPE_OPTION
@SET_OPTION
@LIST_OPTION
@CLEAR_OPTION
@APPEND_OPTION
@GET_OPTION
@REMOVE_OPTION
@UPDATE_OPTION
@MIRROR_OPTION
@BACKUP_OPTION
@RESTORE_OPTION
@VERBOSE_OPTION
@COPY_FROM_OPTION
@click.pass_context
def cli(
    ctx,
    help_,
    debug,
    files,
    walk,
    json_,
    wipe,
    set_,
    list_,
    clear,
    append,
    get,
    remove,
    update,
    mirror,
    backup,
    restore,
    verbose,
    copyfrom,
):
    """ Read/write metadata from file(s). """

    if help_:
        click.echo_via_pager(ctx.get_help())
        ctx.exit(0)

    if debug:
        logging.disable(logging.NOTSET)

    logging.debug(
        f"ctx={ctx} debug={debug} files={files} walk={walk} json={json_} "
        f"set={set_}, list={list_},clear={clear},append={append},get={get}, remove={remove} "
        f"backup={backup}, restore={restore}, mirror={mirror}"
    )

    if not files:
        click.echo(ctx.get_help())
        ctx.exit()

    # validate values for --set, --clear, --append, --get, --remove, --mirror
    if any([set_, append, remove, clear, get, mirror]):
        attributes = (
            [a[0] for a in set_]
            + [a[0] for a in append]
            + list(clear)
            + list(get)
            + list(itertools.chain(*mirror))
        )
        invalid_attr = False
        for attr in attributes:
            if attr not in ATTRIBUTES:
                click.echo(f"Invalid attribute {attr}", err=True)
                invalid_attr = True
        if invalid_attr:
            # click.echo("")  # add a new line before rest of help text
            # click.echo(ctx.get_help())
            ctx.exit(2)

    # check that json_ only used with get or list_
    if json_ and not any([get, list_]):
        click.echo("--json can only be used with --get or --list", err=True)
        # click.echo("")  # add a new line before rest of help text
        # click.echo(ctx.get_help())
        ctx.exit(2)

    # can't backup and restore at once
    if backup and restore:
        click.echo("--backup and --restore cannot be used together", err=True)
        # click.echo("")  # add a new line before rest of help text
        # click.echo(ctx.get_help())
        ctx.exit(2)

    # check compatible types for mirror
    if mirror:
        for item in mirror:
            attr1, attr2 = item
            attribute1 = ATTRIBUTES[attr1]
            attribute2 = ATTRIBUTES[attr2]
            if (
                attribute1.list != attribute2.list
                or attribute1.type_ != attribute2.type_
            ):
                # can only mirror compatible attributes
                click.echo(
                    f"Cannot mirror {attr1}, {attr2}: incompatible types", err=True
                )
                # click.echo("")  # add a new line before rest of help text
                # click.echo(ctx.get_help())
                ctx.exit(2)

    # loop through each file, process it, then do backup or restore if needed
    for filename in files:
        if walk and os.path.isdir(filename):
            for root, _, filenames in os.walk(filename):
                backup_file = pathlib.Path(root) / _BACKUP_FILENAME
                if verbose:
                    click.echo(f"Processing directory {root}")
                if restore:
                    try:
                        backup_data = load_backup_file(backup_file)
                    except FileNotFoundError:
                        click.echo(
                            f"Missing backup file {backup_file} for {root}, skipping restore",
                            err=True,
                        )
                        backup_data = {}
                else:
                    backup_data = {}

                for fname in filenames:
                    fpath = pathlib.Path(f"{root}/{fname}").resolve()
                    if restore and backup_data:
                        try:
                            attr_dict = backup_data[fname]
                            if verbose:
                                click.echo(f"    Restoring attribute data for {fpath}")
                            md = osxmetadata.OSXMetaData(fpath)
                            md._restore_attributes(attr_dict)
                        except:
                            if verbose:
                                click.echo(
                                    f"    Skipping restore for file {fpath}: not in backup file"
                                )

                    if verbose:
                        click.echo(f"  Processing file: {fpath}")

                    process_file(
                        fpath,
                        json_,
                        set_,
                        append,
                        update,
                        remove,
                        clear,
                        get,
                        list_,
                        mirror,
                        wipe,
                        verbose,
                        copyfrom,
                    )

                    if backup:
                        if verbose:
                            click.echo(f"    Backing up attribute data for {fpath}")
                        json_data = osxmetadata.OSXMetaData(fpath)._to_dict()
                        backup_data[fpath.name] = json_data
                if backup:
                    # done walking through files in this folder, write the backup data
                    write_backup_file(backup_file, backup_data)
        elif os.path.isdir(filename):
            # skip directory
            if verbose:
                click.echo(
                    f"skipping directory: {filename}; use --walk to process directories"
                )
            continue
        else:
            fpath = pathlib.Path(filename).resolve()
            backup_file = pathlib.Path(pathlib.Path(filename).parent) / _BACKUP_FILENAME
            if restore:
                try:
                    backup_data = load_backup_file(backup_file)
                    attr_dict = backup_data[pathlib.Path(fpath).name]
                    if verbose:
                        click.echo(f"  Restoring attribute data for {fpath}")
                    md = osxmetadata.OSXMetaData(fpath)
                    md._restore_attributes(attr_dict)
                except FileNotFoundError:
                    click.echo(
                        f"Missing backup file {backup_file} for {fpath}, skipping restore",
                        err=True,
                    )
                except KeyError:
                    if verbose:
                        click.echo(
                            f"      Skipping restore for file {fpath}: not in backup file"
                        )

            if verbose:
                click.echo(f"Processing file: {fpath}")

            process_file(
                fpath,
                json_,
                set_,
                append,
                update,
                remove,
                clear,
                get,
                list_,
                mirror,
                wipe,
                verbose,
                copyfrom,
            )

            if backup:
                if verbose:
                    click.echo(f"  Backing up attribute data for {fpath}")
                # load the file if it exists, merge new data, then write out the file again
                if backup_file.is_file():
                    backup_data = load_backup_file(backup_file)
                else:
                    backup_data = {}
                json_dict = osxmetadata.OSXMetaData(fpath)._to_dict()
                backup_data[pathlib.Path(fpath).name] = json_dict
                write_backup_file(backup_file, backup_data)


def process_file(
    fpath,
    json_,
    set_,
    append,
    update,
    remove,
    clear,
    get,
    list_,
    mirror,
    wipe,
    verbose,
    copyfrom,
):
    """ process a single file to apply the options 
        options processed in this order: wipe, copyfrom, clear, set, append, remove, mirror, get, list
        Note: expects all attributes passed in parameters to be validated as valid attributes """

    logging.debug(f"process_file: {fpath}")

    md = osxmetadata.OSXMetaData(fpath)

    if wipe:
        attr_list = md.list_metadata()
        if verbose and attr_list:
            click.echo(f"Wiping metadata from {fpath}")
        elif verbose:
            click.echo(f"No metadata to wipe from {fpath}")
        for attr in attr_list:
            try:
                attribute = ATTRIBUTES[attr]
                if verbose:
                    click.echo(f"  Wiping {attr} from {fpath}")
                md.clear_attribute(attribute.name)
            except KeyError:
                if verbose:
                    click.echo(
                        f"  Unknown attribute {attr} on {fpath}, skipping", err=True
                    )

    if copyfrom:
        if verbose:
            click.echo(f"Copying attributes from {copyfrom}")
        src_md = osxmetadata.OSXMetaData(copyfrom)
        for attr in src_md.list_metadata():
            if verbose:
                click.echo(f"  Copying {attr}")
            md.set_attribute(attr, src_md.get_attribute(attr))

    if clear:
        for attr in clear:
            attribute = ATTRIBUTES[attr]
            if verbose:
                click.echo(f"Clearing {attr}")
            md.clear_attribute(attribute.name)

    if set_:
        # set data
        # check attribute is valid
        attr_dict = {}
        for item in set_:
            attr, val = item
            attribute = ATTRIBUTES[attr]
            if verbose:
                click.echo(f"Setting {attr}={val}")
            try:
                attr_dict[attribute].append(val)
            except KeyError:
                attr_dict[attribute] = [val]

        for attribute, value in attr_dict.items():
            md.set_attribute(attribute.name, value)

    if append:
        # append data
        # check attribute is valid
        attr_dict = {}
        for item in append:
            attr, val = item
            attribute = ATTRIBUTES[attr]
            if verbose:
                click.echo(f"Appending {attr}={val}")
            try:
                attr_dict[attribute].append(val)
            except KeyError:
                attr_dict[attribute] = [val]

        for attribute, value in attr_dict.items():
            md.append_attribute(attribute.name, value)

    if update:
        # update data
        # check attribute is valid
        attr_dict = {}
        for item in update:
            attr, val = item
            attribute = ATTRIBUTES[attr]
            if verbose:
                click.echo(f"Updating {attr}={val}")
            try:
                attr_dict[attribute].append(val)
            except KeyError:
                attr_dict[attribute] = [val]

        for attribute, value in attr_dict.items():
            md.update_attribute(attribute.name, value)

    if remove:
        # remove value from attribute
        # actually implemented with discard so no error raised if not present
        # todo: catch errors and display help
        for attr, val in remove:
            try:
                if verbose:
                    click.echo(f"Removing {attr}")
                attribute = ATTRIBUTES[attr]
                md.discard_attribute(attribute.name, val)
            except KeyError as e:
                raise e

    if mirror:
        for item in mirror:
            # mirror value of each attribute
            # validation that attributes are compatible
            # will have occured prior to call to process_file
            attr1, attr2 = item
            if verbose:
                click.echo(f"Mirroring {attr1} {attr2}")
            attribute1 = ATTRIBUTES[attr1]

            if attribute1.list:
                # merge the two lists, assume attribute2 also a list due to
                # previous validation
                # update attr2 with any new values from attr1
                # then set attr1 = attr2
                attr1_values = md.get_attribute(attr1)
                md.update_attribute(attr2, attr1_values)
                md.set_attribute(attr1, md.get_attribute(attr2))
            else:
                md.set_attribute(attr1, md.get_attribute(attr2))

    if get:
        logging.debug(f"get: {get}")
        if json_:
            data = {}
            data["_version"] = __version__
            data["_filepath"] = fpath.resolve().as_posix()
            data["_filename"] = fpath.name
        for attr in get:
            attribute = ATTRIBUTES[attr]
            if json_:
                if attribute.type_ == datetime.datetime:
                    # need to convert datetime.datetime to string to serialize
                    value = md.get_attribute(attribute.name)
                    if type(value) == list:
                        value = [v.isoformat() for v in value]
                    else:
                        value = value.isoformat()
                    data[attribute.constant] = value
                else:
                    # get raw value
                    data[attribute.constant] = md.get_attribute(attribute.name)
            else:
                value = md.get_attribute_str(attribute.name)
                click.echo(
                    f"{attribute.name:{_SHORT_NAME_WIDTH}}{attribute.constant:{_LONG_NAME_WIDTH}} = {value}"
                )
        if json_:
            json_str = json.dumps(data)
            click.echo(json_str)

    if list_:
        if json_:
            json_str = md.to_json()
            click.echo(json_str)
        else:
            attribute_list = md.list_metadata()
            for attr in attribute_list:
                try:
                    attribute = ATTRIBUTES[attr]
                    value = md.get_attribute_str(attribute.name)
                    click.echo(
                        f"{attribute.name:{_SHORT_NAME_WIDTH}}{attribute.constant:{_LONG_NAME_WIDTH}} = {value}"
                    )
                except KeyError:
                    click.echo(
                        f"{'UNKNOWN':{_SHORT_NAME_WIDTH}}{attr:{_LONG_NAME_WIDTH}} = THIS ATTRIBUTE NOT HANDLED",
                        err=True,
                    )


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
