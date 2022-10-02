"""CLI for osxmetadata"""

import datetime
import glob
import itertools
import json
import logging
import os
import os.path
import pathlib
import typing as t

import click

from osxmetadata import (
    ALL_ATTRIBUTES,
    OSXMetaData,
    Tag,
    _kFinderColor,
    _kFinderInfo,
    _kFinderStationeryPad,
    _kMDItemUserTags,
    __version__,
    MDIMPORTER_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_READ_ONLY,
)
from osxmetadata.backup import get_backup_dict, load_backup_file, write_backup_file
from osxmetadata.constants import (
    _COLORNAMES_LOWER,
    _FINDERINFO_NAMES,
    _TAGS_NAMES,
    FINDER_COLOR_NONE,
)
from osxmetadata.finder_tags import tag_factory

# TODO: how is metadata on symlink handled?
# should symlink be resolved before gathering metadata?
# currently, symlinks are resolved before handling metadata but not sure this is the right behavior
# in 10.13.6: synlinks appear to inherit tags but not Finder Comments:
#   e.g. changes to tags in a file changes tags in the symlink but symlink can have it's own finder comment
#   Finder aliases inherit neither
# TODO: add selective restore (e.g only restore files matching command line path)
#   e.g osxmetadata -r meta.json *.pdf

_SHORT_NAME_WIDTH = (
    max(len(x["short_name"]) for x in MDITEM_ATTRIBUTE_DATA.values()) + 1
)
_LONG_NAME_WIDTH = max(len(x["name"]) for x in MDITEM_ATTRIBUTE_DATA.values()) + 1

_BACKUP_FILENAME = ".osxmetadata.json"


def get_writeable_attributes() -> t.List[str]:
    """Return a list of writeable attributes"""
    no_write = ["kMDItemContentCreationDate", "kMDItemContentModificationDate"]
    write = [
        *MDITEM_ATTRIBUTE_DATA.keys(),
        _kFinderColor,
        _kFinderStationeryPad,
        _kMDItemUserTags,
    ]
    return [
        attr
        for attr in write
        if attr not in MDITEM_ATTRIBUTE_READ_ONLY and attr not in no_write
    ]


WRITABLE_ATTRIBUTES = get_writeable_attributes()


def value_to_str(value) -> str:
    """Convert a metadata value to str suitable for printing to terminal"""
    if isinstance(value, str):
        return value
    elif value is None:
        return "(null)"
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    elif isinstance(value, (list, tuple)):
        if not value:
            return "(empty list)"
        if isinstance(value[0], str):
            return ", ".join(value)
        elif isinstance(value[0], Tag):
            return ", ".join(f"{x.name}: {x.color}" for x in value)
        elif isinstance(value[0], datetime.datetime):
            return ", ".join(x.isoformat() for x in value)
        else:
            return ", ".join(str(x) for x in value)
    else:
        return str(value)


def get_attributes_to_wipe(mdobj: OSXMetaData) -> t.List[str]:
    """Get list of non-null metadata attributes on a file that can be wiped"""

    attribute_list = []
    for attr in WRITABLE_ATTRIBUTES:
        if value := mdobj.get(attr):
            attribute_list.append(attr)
    return attribute_list


# Click CLI object & context settings
class CLI_Obj:
    def __init__(self, debug=False, files=None):
        self.debug = debug
        self.files = files


class MyClickCommand(click.Command):
    """Custom click.Command that overrides get_help() to show additional info"""

    def get_help(self, ctx):
        help_text = super().get_help(ctx)
        formatter = click.HelpFormatter()

        # build help text from all the attribute names
        # passed to click.HelpFormatter.write_dl for formatting
        attr_tuples = [("Short Name", "Description")]
        for attr in sorted(set(MDITEM_ATTRIBUTE_DATA.keys())):

            # get short and long name
            short_name = MDITEM_ATTRIBUTE_DATA[attr]["short_name"]
            long_name = MDITEM_ATTRIBUTE_DATA[attr]["name"]
            constant = MDITEM_ATTRIBUTE_DATA[attr]["xattr_constant"]

            # get help text
            description = MDITEM_ATTRIBUTE_DATA[attr]["description"]
            type_ = MDITEM_ATTRIBUTE_DATA[attr]["help_type"]
            attr_help = f"{long_name}; {constant}; {description}; {type_}"

            # add to list
            attr_tuples.append((short_name, attr_help))

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
        formatter.write_text(
            "Finder tags (tags attribute) contain both a name and an optional color. "
            + "To specify the color, append comma + color name (e.g. 'red') after the "
            + "tag name.  For example --set tags Foo,red. "
            + "Valid color names are: "
            + f"{', '.join([color for color, colorid in _COLORNAMES_LOWER.items() if colorid != FINDER_COLOR_NONE])}. "
            + "If color is not specified but a tag of the same name has already been assigned a color "
            + "in the Finder, the same color will automatically be assigned. "
        )
        formatter.write("\n")
        formatter.write_text(
            "com.apple.FinderInfo (finderinfo) value is a key:value dictionary. "
            + "To set finderinfo, pass value in format key1:value1,key2:value2,etc. "
            + "For example: 'osxmetadata --set finderinfo color:2 file.ext'."
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
    "Backup file '.osxmetadata.json' will be created in same folder as FILE. "
    "Only backs up attributes known to osxmetadata unless used with --all.",
    is_flag=True,
    required=False,
    default=False,
)
RESTORE_OPTION = click.option(
    "--restore",
    "-R",
    help="Restore FILE attributes from backup file.  "
    "Restore will look for backup file '.osxmetadata.json' in same folder as FILE. "
    "Only restores attributes known to osxmetadata unless used with --all.",
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
    help="Copy attributes from file SOURCE_FILE (only updates destination attributes that are not null in SOURCE_FILE).",
    type=click.Path(exists=True),
    nargs=1,
    multiple=False,
    required=False,
)
FILES_ONLY_OPTION = click.option(
    "--files-only",
    help="Do not apply metadata commands to directories themselves, only files in a directory.",
    is_flag=True,
    default=False,
    required=False,
)
PATTERN_OPTION = click.option(
    "--pattern",
    "-p",
    metavar="PATTERN",
    help="Only process files matching PATTERN; only applies to --walk. "
    "If specified, only files matching PATTERN will be processed as each directory is walked. "
    "May be used for than once to specify multiple patterns. "
    "For example, tag all *.pdf files in projectdir and subfolders with tag 'project': "
    "osxmetadata --append tags 'project' --walk projectdir/ --pattern '*.pdf'",
    multiple=True,
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
@FILES_ONLY_OPTION
@PATTERN_OPTION
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
    files_only,
    pattern,
):
    """Read/write metadata from file(s)."""

    if help_:
        click.echo_via_pager(ctx.get_help())
        ctx.exit(0)

    if debug:
        logging.disable(logging.NOTSET)

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
            if attr not in ALL_ATTRIBUTES:
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
            attribute1 = MDITEM_ATTRIBUTE_DATA[attr1]
            attribute2 = MDITEM_ATTRIBUTE_DATA[attr2]

            # avoid self mirroring
            if attribute1 == attribute2:
                click.echo(
                    f"cannot mirror the same attribute: {attribute1.name} {attribute2.name}",
                    err=True,
                )
                ctx.get_help()
                ctx.exit(2)

            # check type compatibility
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
        if not all([os.path.isdir(filename), walk, pattern]):
            process_files(
                ctx,
                [filename],
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
                backup,
                restore,
                walk,
                files_only,
            )

        if walk and os.path.isdir(filename):
            for root, dirnames, filenames in os.walk(filename):
                if pattern:
                    # only process files matching pattern
                    filepaths = []
                    for dirname in dirnames:
                        for matches in [
                            glob.glob(os.path.join(os.path.join(root, dirname), pat))
                            for pat in pattern
                        ]:
                            filepaths.extend(matches)
                else:
                    filepaths = [
                        os.path.join(root, fname) for fname in dirnames + filenames
                    ]
                process_files(
                    ctx,
                    filepaths,
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
                    backup,
                    restore,
                    walk,
                    files_only,
                )


def process_files(
    ctx,
    files,
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
    backup,
    restore,
    walk,
    files_only,
):
    """process list of files, calls process_single_file to process each file
    options processed in this order: wipe, copyfrom, clear, set, append, remove, mirror, get, list
    Note: expects all attributes passed in parameters to be validated as valid attributes
    """
    for filename in files:
        fpath = pathlib.Path(filename).resolve()
        backup_file = pathlib.Path(pathlib.Path(filename).parent) / _BACKUP_FILENAME

        if files_only and fpath.is_dir():
            if verbose:
                click.echo(f"Skipping directory: {fpath}")
            continue

        if verbose:
            click.echo(f"Processing file: {fpath}")

        if restore:
            try:
                backup_data = load_backup_file(backup_file)
                attr_dict = backup_data[pathlib.Path(fpath).name]
                if verbose:
                    click.echo(f"  Restoring attribute data for {fpath}")
                md = OSXMetaData(fpath)
                md._restore_attributes(attr_dict)
            except FileNotFoundError:
                click.echo(
                    f"Missing backup file {backup_file} for {fpath}, skipping restore",
                    err=True,
                )
            except KeyError:
                if verbose:
                    click.echo(
                        f"  Skipping restore for file {fpath}: not in backup file"
                    )

        process_single_file(
            ctx,
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
            # TODO: this is ripe for refactoring with a sqlite database
            # Currently, the code writes the entire backup database each time a file is processed
            if verbose:
                click.echo(f"  Backing up attribute data for {fpath}")
            # load the file if it exists, merge new data, then write out the file again
            backup_data = load_backup_file(backup_file) if backup_file.is_file() else {}
            backup_dict = get_backup_dict(fpath)
            backup_data[pathlib.Path(fpath).name] = backup_dict
            write_backup_file(backup_file, backup_data)


def process_single_file(
    ctx,
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
    """process a single file to apply the options
    options processed in this order: wipe, copyfrom, clear, set, append, remove, mirror, get, list
    Note: expects all attributes passed in parameters to be validated as valid attributes"""

    md = OSXMetaData(fpath)

    if wipe:
        attr_list = get_attributes_to_wipe(md)
        if verbose:
            if attr_list:
                click.echo(f"Wiping metadata from {fpath}")
            else:
                click.echo(f"No metadata to wipe from {fpath}")
        for attr in attr_list:
            try:
                if verbose:
                    click.echo(f"  Wiping {attr} from {fpath}")
                md.set(attr, None)
            except AttributeError:
                if verbose:
                    click.echo(
                        f"  Unknown attribute {attr} on {fpath}, skipping", err=True
                    )

    if copyfrom:
        if verbose:
            click.echo(f"Copying attributes from {copyfrom}")
        src_md = OSXMetaData(copyfrom)
        for attr in WRITABLE_ATTRIBUTES:
            if value := src_md.get(attr):
                if verbose:
                    click.echo(f"  Copying {attr}")
                md.set(attr, value)

    if clear:
        for attr in clear:
            if verbose:
                click.echo(f"Clearing {attr}")
            if not md.get(attr):
                if verbose:
                    click.echo(f"  {attr} is already empty on {fpath}")
                continue
            md.set(attr, None)

    if set_:
        # set data
        # check attribute is valid
        attr_dict = {}
        for item in set_:
            attr, val = item
            attribute = MDITEM_ATTRIBUTE_DATA[attr]

            if attr in _TAGS_NAMES:
                val = tag_factory(val)
            elif attr in _FINDERINFO_NAMES:
                val = _AttributeFinderInfo._str_to_value_dict(val)

            if verbose:
                click.echo(f"Setting {attr}={val}")
            try:
                attr_dict[attribute].append(val)
            except KeyError:
                attr_dict[attribute] = [val]

        for attribute, value in attr_dict.items():
            if attribute.list:
                # attribute expects a list so pass value (which is a list)
                md.set_attribute(attribute.name, value)
            elif len(value) == 1:
                # expected one and got one
                md.set_attribute(attribute.name, value[0])
            else:
                click.echo(
                    f"attribute {attribute.name} expects only a single value but {len(value)} provided",
                    err=True,
                )
                ctx.get_help()
                ctx.exit(2)

    if append:
        # append data
        # check attribute is valid
        attr_dict = {}
        for item in append:
            attr, val = item
            attribute = MDITEM_ATTRIBUTE_DATA[attr]

            if not attribute.append:
                click.echo(
                    f"append is not a valid operation for attribute {attribute.name}",
                    err=True,
                )
                ctx.get_help()
                ctx.exit(2)

            if attr in [*_TAGS_NAMES, *_FINDERINFO_NAMES]:
                val = tag_factory(val)

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
            attribute = MDITEM_ATTRIBUTE_DATA[attr]

            if not attribute.update:
                click.echo(
                    f"update is not a valid operation for attribute {attribute.name}",
                    err=True,
                )
                ctx.get_help()
                ctx.exit(2)

            if attr in [*_TAGS_NAMES, *_FINDERINFO_NAMES]:
                val = tag_factory(val)

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
        for attr, val in remove:
            attribute = MDITEM_ATTRIBUTE_DATA[attr]
            if not attribute.list:
                click.echo(
                    f"remove is not a valid operation for single-value attributes",
                    err=True,
                )
                ctx.get_help()
                ctx.exit(2)

            if attr in [*_TAGS_NAMES, *_FINDERINFO_NAMES]:
                val = tag_factory(val)
            if verbose:
                click.echo(f"Removing {attr}")
            try:
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

            attribute1 = MDITEM_ATTRIBUTE_DATA[attr1]
            attribute2 = MDITEM_ATTRIBUTE_DATA[attr2]

            if attribute1.name == "tags":
                tags = md.get_attribute(attr1)
                attr1_values = [tag.name for tag in tags]
                md.update_attribute(attr2, attr1_values)
                md.set_attribute(attr1, [Tag(val) for val in md.get_attribute(attr2)])
            elif attribute2.name == "tags":
                attr1_values = md.get_attribute(attr1)
                md.update_attribute(attr2, [Tag(val) for val in attr1_values])
                tags = md.get_attribute(attr2)
                attr2_values = [tag.name for tag in tags]
                md.set_attribute(attr1, attr2_values)
            elif attribute1.list:
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
        data = {}
        if json_:
            data["_version"] = __version__
            data["_filepath"] = fpath.resolve().as_posix()
            data["_filename"] = fpath.name
        for attr in get:
            attribute = MDITEM_ATTRIBUTE_DATA[attr]
            if json_:
                try:
                    if attribute.name == "tags":
                        tags = md.get_attribute(attribute.name)
                        value = [[tag.name, tag.color] for tag in tags]
                        data[attribute.constant] = value
                    elif (
                        attribute.name == "finderinfo"
                        or attribute.type_ != datetime.datetime
                    ):
                        data[attribute.constant] = md.get_attribute(attribute.name)
                    else:
                        # need to convert datetime.datetime to string to serialize
                        value = md.get_attribute(attribute.name)
                        if type(value) == list:
                            value = [v.isoformat() for v in value]
                        else:
                            value = value.isoformat()
                        data[attribute.constant] = value
                except KeyError:
                    # unknown attribute, ignore it
                    pass
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
            click.echo(f"{fpath}:")
            for attr in md.asdict():
                try:
                    value = md.get(attr)
                    if value is None or value == "" or value == []:
                        continue
                    value = value_to_str(value)
                    if attr in MDITEM_ATTRIBUTE_DATA:
                        attribute = MDITEM_ATTRIBUTE_DATA[attr]
                        short_name = attribute["short_name"]
                        name = attribute["name"]
                    elif attr in MDIMPORTER_ATTRIBUTE_DATA:
                        attribute = MDIMPORTER_ATTRIBUTE_DATA[attr]
                        short_name = attribute["name"]
                        name = attribute["name"]
                    elif attr in [_kFinderInfo, _kFinderColor, _kFinderStationeryPad]:
                        short_name = attr
                        name = attr
                    elif attr == _kMDItemUserTags:
                        short_name = "tags"
                        name = _kMDItemUserTags
                    else:
                        click.echo(
                            f"{'UNKNOWN ATTRIBUTE':{_SHORT_NAME_WIDTH}}{attr:{_LONG_NAME_WIDTH}} = THIS ATTRIBUTE NOT HANDLED",
                            err=True,
                        )
                    click.echo(
                        f"{short_name:{_SHORT_NAME_WIDTH}}{name:{_LONG_NAME_WIDTH}} = {value}"
                    )
                except Exception as e:
                    click.echo(
                        f"{'Error loading attribute':{_SHORT_NAME_WIDTH}}{attr:{_LONG_NAME_WIDTH}}: {e}",
                        err=True,
                    )


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
