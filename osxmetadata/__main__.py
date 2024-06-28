"""CLI for osxmetadata"""

import datetime
import glob
import json
import logging
import os
import os.path
import pathlib
import typing as t

import click

from osxmetadata import (
    ALL_ATTRIBUTES,
    MDIMPORTER_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_DATA,
    MDITEM_ATTRIBUTE_READ_ONLY,
    MDITEM_ATTRIBUTE_SHORT_NAMES,
    OSXMetaData,
    Tag,
    __version__,
    _kFinderColor,
    _kFinderInfo,
    _kFinderStationeryPad,
    _kMDItemUserTags,
)
from osxmetadata.backup import get_backup_dict, load_backup_file, write_backup_file
from osxmetadata.constants import _COLORNAMES_LOWER, _TAGS_NAMES, FINDER_COLOR_NONE
from osxmetadata.finder_info import str_to_finder_color
from osxmetadata.finder_tags import tag_factory
from osxmetadata.mditem import str_to_mditem_type

# TODO: how is metadata on symlink handled?
# should symlink be resolved before gathering metadata?
# currently, symlinks are resolved before handling metadata but not sure this is the right behavior
# in 10.13.6: synlinks appear to inherit tags but not Finder Comments:
#   e.g. changes to tags in a file changes tags in the symlink but symlink can have it's own finder comment
#   Finder aliases inherit neither
# TODO: add selective restore (e.g only restore files matching command line path)
#   e.g osxmetadata -r meta.json *.pdf

# TODO: fix output of str_to_mditem_type to be more helpful: ValueError: Invalid isoformat string: '2022-10-6'
# also wrap in try/except and print error message

_SHORT_NAME_WIDTH = (
    max(len(x["short_name"]) for x in MDITEM_ATTRIBUTE_DATA.values()) + 1
)
_LONG_NAME_WIDTH = max(len(x["name"]) for x in MDITEM_ATTRIBUTE_DATA.values()) + 1

BACKUP_FILENAME = ".osxmetadata.json"


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


def get_attribute_type(attr: str) -> t.Optional[str]:
    """Get the type of an attribute

    Args:
        attr: attribute name

    Returns:
        type of attribute as string or None if type is not known
    """
    if attr in MDITEM_ATTRIBUTE_SHORT_NAMES:
        attr = MDITEM_ATTRIBUTE_SHORT_NAMES[attr]
    return (
        "list"
        if attr in _TAGS_NAMES
        else (
            MDITEM_ATTRIBUTE_DATA[attr]["python_type"]
            if attr in MDITEM_ATTRIBUTE_DATA
            else (
                "int"
                if attr == _kFinderColor
                else "bool" if attr == _kFinderStationeryPad else None
            )
        )
    )


def get_attribute_name(attr: str) -> str:
    """Get the long name of an attribute

    Args:
        attr: attribute name

    Returns:
        long name of attribute or attr if long name is not known
    """
    if attr in MDITEM_ATTRIBUTE_SHORT_NAMES:
        return MDITEM_ATTRIBUTE_SHORT_NAMES[attr]
    elif attr in MDITEM_ATTRIBUTE_DATA:
        return attr
    elif attr in MDIMPORTER_ATTRIBUTE_DATA:
        return attr
    elif attr in _TAGS_NAMES:
        return _kMDItemUserTags
    elif attr in [_kFinderColor, _kFinderStationeryPad]:
        return attr
    else:
        raise ValueError(f"Unknown attribute: {attr}")


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


def str_to_bool(value: str) -> bool:
    """Convert str value to bool:

    Args:
        value: str value to convert to bool

    Returns: True if str value is "True" or "true", or non-zero int; False otherwise
    """
    try:
        return bool(int(value))
    except ValueError:
        return value.lower() == "true"


def get_attributes_to_wipe(md: OSXMetaData) -> t.List[str]:
    """Get list of non-null metadata attributes on a file that can be wiped"""

    attribute_list = []
    for attr in WRITABLE_ATTRIBUTES:
        if value := md.get(attr):
            attribute_list.append(attr)
    return attribute_list


def md_wipe_metadata(md: OSXMetaData, verbose: bool = False):
    """Wipe metadata attributes on a file

    Args:
        md: OSXMetaData object for file
        attributes: list of attributes to wipe
        verbose: if True, print verbose output
    """
    attr_list = get_attributes_to_wipe(md)
    filepath = md.path
    if verbose:
        if attr_list:
            click.echo(f"Wiping metadata from {filepath}")
        else:
            click.echo(f"No metadata to wipe from {filepath}")
    for attr in attr_list:
        try:
            if verbose:
                click.echo(f"  Wiping {attr} from {filepath}")
            md.set(attr, None)
        except AttributeError:
            if verbose:
                click.echo(
                    f"  Unknown attribute {attr} on {filepath}, skipping", err=True
                )


def validate_attribute_names(attributes: t.Union[t.Tuple[str], t.Tuple[str, str]]):
    """Validate attribute names as returned by click option parsing:

    Args:
        attributes: tuple of attribute names or tuple of attribute name and value

    Returns:
        True if valid, raises click.BadParameter if not
    """

    for attr in attributes:
        if isinstance(attr, tuple):
            attr = attr[0]
        if attr not in ALL_ATTRIBUTES:
            raise click.BadParameter(f"Invalid attribute name: {attr}")


def get_attribute_names(attribute: str) -> t.Tuple[str, str]:
    """Get the name and short name for a metadata attribute

    Args:
        attribute: attribute name or short name

    Returns:
        tuple of attribute name and short name
    """
    if attribute in MDITEM_ATTRIBUTE_DATA:
        attribute = MDITEM_ATTRIBUTE_DATA[attribute]
        short_name = attribute["short_name"]
        name = attribute["name"]
    elif attribute in MDITEM_ATTRIBUTE_SHORT_NAMES:
        short_name = attribute
        name = MDITEM_ATTRIBUTE_SHORT_NAMES[attribute]
    elif attribute in MDIMPORTER_ATTRIBUTE_DATA:
        attribute = MDIMPORTER_ATTRIBUTE_DATA[attribute]
        short_name = attribute["name"]
        name = attribute["name"]
    elif attribute in [_kFinderInfo, _kFinderColor, _kFinderStationeryPad]:
        short_name = attribute
        name = attribute
    elif attribute in _TAGS_NAMES:
        short_name = "tags"
        name = _kMDItemUserTags
    else:
        raise ValueError(f"Unknown attribute: {attribute}")

    return name, short_name


def md_copyfrom_metadata(md: OSXMetaData, copyfrom: str, verbose: bool = False):
    """Copy metadata attributes to a file from another file

    Args:
        md: OSXMetaData object for destination file
        copyfrom: path to source file
        verbose: if True, print verbose output
    """
    if verbose:
        click.echo(f"Copying attributes from {copyfrom}")
    src_md = OSXMetaData(copyfrom)
    for attr in WRITABLE_ATTRIBUTES:
        if value := src_md.get(attr):
            if verbose:
                click.echo(f"  Copying {attr}")
            md.set(attr, value)


def md_clear_metadata(
    md: OSXMetaData, tr, attributes: t.List[str], verbose: bool = False
):
    """Clear metadata attributes on a file

    Args:
        md: OSXMetaData object for file
        attributes: list of attributes to clear
        verbose: if True, print verbose output
    """
    for attr in attributes:
        if verbose:
            click.echo(f"Clearing {attr}")
        if not md.get(attr):
            if verbose:
                click.echo(f"  {attr} is already empty on {md.path}")
            continue
        md.set(attr, None)


def md_set_metadata_with_error(
    md: OSXMetaData, metadata: t.Tuple[t.Tuple[str, str]], verbose: bool
) -> t.Optional[str]:
    """Set metadata for OSXMetaData object, return error message if any

    Args:
        md: OSXMetaData object
        metadata: tuple of tuples of (attribute, value) as returned by click parser
        verbose: if True, print metadata being set

    Returns:
        None if successful, else error message
    """

    attr_dict = {}
    for item in metadata:
        attr, val = item
        val = val or None

        # Convert attribute shortcut name to long name if necessary
        attr = get_attribute_name(attr)

        if attr in _TAGS_NAMES:
            val = tag_factory(val) if val else None
        elif attr == _kFinderColor:
            val = str_to_finder_color(val)
        elif attr == _kFinderStationeryPad:
            val = str_to_bool(val)
        elif attr in MDITEM_ATTRIBUTE_DATA:
            val = str_to_mditem_type(attr, val)
        else:
            return f"Invalid attribute: {attr}"

        if attr in attr_dict:
            attr_dict[attr].append(val)
        else:
            attr_dict[attr] = [val]

    for attribute, value in attr_dict.items():
        # if we got a list of values and attribute takes a list, set the list
        # otherwise, set the last value in the list
        if verbose:
            click.echo(f"Setting {attribute}={value}")
        if get_attribute_type(attribute) in ["list", "list[datetime.datetime]"]:
            # filter out any None values ([None] should be [])
            value = [v for v in value if v is not None]
            md.set(attribute, value)
        else:
            md.set(attribute, value[-1])

    return None


def md_append_metadata_with_error(
    md: OSXMetaData, metadata: t.List[t.Tuple[str, str]], verbose: bool
) -> t.Optional[str]:
    """Append metadata attributes on a file

    Args:
        md: OSXMetaData object for file
        metadata: list of tuples of (attribute, value) as returned by click parser
        verbose: if True, print verbose output

    Returns:
        None if successful, else error message
    """
    for attr, val in metadata:
        if verbose:
            click.echo(f"Appending {attr}={val}")

        # Convert attribute shortcut name to long name if necessary
        attr = get_attribute_name(attr)

        if attr in _TAGS_NAMES:
            value = tag_factory(val)
        elif attr in MDITEM_ATTRIBUTE_DATA:
            value = str_to_mditem_type(attr, val)
        else:
            # other types like _kFinderColor cannot be appended to
            return f"Invalid attribute: {attr}"

        attr_type = get_attribute_type(attr)

        if attr_type in ["list", "list[datetime.datetime]"]:
            new_value = md.get(attr) or []
            if value not in new_value:
                new_value.append(value)
                md.set(attr, new_value)
            elif verbose:
                click.echo(f"  {attr} already contains {val}")
        elif attr_type == "str":
            new_value = md.get(attr) or ""
            md.set(attr, new_value + value)
        else:
            return f"Attribute {attr} does not support appending"

    return None


def md_remove_metadata_with_error(
    md: OSXMetaData, metadata: t.List[t.Tuple[str, str]], verbose: bool
) -> t.Optional[str]:
    """ "Remove metadata attributes on a file

    Args:
        md: OSXMetaData object for file
        metadata: list of tuples of (attribute, value) as returned by click parser
        verbose: if True, print verbose output

    Returns:
        None if successful, else error message
    """
    for attr, val in metadata:
        attr_type = get_attribute_type(attr)
        if attr_type not in ["list", "list[datetime.datetime]"]:
            return f"remove is not a valid operation for single-value attribute {attr}"

        if attr in _TAGS_NAMES:
            val = md_tag_value_from_file(md, val)
            val = tag_factory(val)
        elif attr in MDITEM_ATTRIBUTE_DATA or attr in MDITEM_ATTRIBUTE_SHORT_NAMES:
            val = str_to_mditem_type(attr, val)
        else:
            return f"Invalid attribute: {attr}"

        new_value = md.get(attr) or []
        new_value = [v for v in new_value if v != val]

        if verbose:
            click.echo(f"Removing {val} from {attr}")
        try:
            md.set(attr, new_value)
        except KeyError as e:
            raise e


def md_tag_value_from_file(md: OSXMetaData, value: str) -> str:
    """Given a tag value, return the tag + color if tag value contains color.
    If not, check if file has the same tag and if so, return the tag + color from the file

    Returns the new tag value
    """
    values = value.split(",")
    if len(values) > 2:
        raise ValueError(f"More than one value found after comma: {value}")
    if len(values) == 2:
        return value
    if file_tags := md.get(_kMDItemUserTags):
        for tag in file_tags:
            if tag.name.lower() == value.lower():
                return f"{value},{tag.color}"
    return value


def md_mirror_metadata_with_error(
    md: OSXMetaData, attributes: t.Tuple[t.Tuple[str, str]], verbose: bool
) -> t.Optional[str]:
    """Mirror metadata attributes on a file

    Args:
        md: OSXMetaData object for file
        attributes: tuple of attribute tuples to mirror as returned by click parser for --mirror
        verbose: if True, print verbose output

    Returns:
        None if successful, else error message
    """
    for item in attributes:
        attr1, attr2 = item
        if verbose:
            click.echo(f"Mirroring {attr1} {attr2}")

        attr_type1 = get_attribute_type(attr1)
        attr_type2 = get_attribute_type(attr2)

        if attr_type1 != attr_type2:
            return f"Attributes {attr1} and {attr2} are not compatible"

        if attr_type1 in ["list", "list[datetime.datetime]"]:
            value1 = md.get(attr1) or []
            value2 = md.get(attr2) or []
            if attr1 in _TAGS_NAMES and attr2 not in _TAGS_NAMES:
                # might be mirroring a keyword to a tag
                # convert non-tags to tags
                value2_tags = [tag_factory(v) for v in value2]
                value1 = value1 + value2_tags
                value2 = value2 + [v.name for v in value1 if v.name not in value2]
                md.set(attr1, value1)
                md.set(attr2, value2)
            elif attr2 in _TAGS_NAMES and attr1 not in _TAGS_NAMES:
                # might be mirroring a tag to a keyword
                # convert tags to non-tags
                value1_tags = [tag_factory(v) for v in value1]
                value2 = value2 + value1_tags
                value1 = value1 + [v.name for v in value2 if v.name not in value1]
                md.set(attr1, value1)
                md.set(attr2, value2)
            elif value1 != value2:
                new_value = value1 + [v for v in value2 if v not in value1]
                md.set(attr1, new_value)
                md.set(attr2, new_value)
        else:
            md.set(attr1, md.get(attr2))

        return None


def md_list_metadata_with_error(md: OSXMetaData, json_: bool) -> t.Optional[str]:
    """List metadata attributes on a file

    Args:
        md: OSXMetaData object for file
        json_: if True, print output as JSON
        verbose: if True, print verbose output

    Returns:
        None if successful, else error message
    """
    if json_:
        json_str = md.to_json()
        click.echo(json_str)
        return

    # print in readable format, not json
    click.echo(f"{md.path}:")
    for attr in sorted(md.asdict()):
        try:
            value = md.get(attr)
            if value is None or value == "" or value == []:
                continue
            value = value_to_str(value)
        except Exception as e:
            click.echo(
                f"{'Error loading attribute':{_SHORT_NAME_WIDTH}}{attr:{_LONG_NAME_WIDTH}}: {e}",
                err=True,
            )
        else:
            try:
                name, short_name = get_attribute_names(attr)
            except ValueError:
                click.echo(
                    f"{'UNKNOWN ATTRIBUTE':{_SHORT_NAME_WIDTH}}{attr:{_LONG_NAME_WIDTH}} = THIS ATTRIBUTE NOT HANDLED",
                    err=True,
                )
            else:
                click.echo(
                    f"{short_name:{_SHORT_NAME_WIDTH}}{name:{_LONG_NAME_WIDTH}} = {value}"
                )


def md_get_metadata_with_error(
    md: OSXMetaData, attributes: t.Tuple[str], json_: bool
) -> t.Optional[str]:
    """Get metadata attribute on a file

    Args:
        md: OSXMetaData object for file
        attributes: tuple of attributes to get as returned by click parser for --get
        json_: if True, print output as JSON

    Returns:
        None if successful, else error message
    """
    data = {}
    if json_:
        data["_version"] = __version__
        data["_filepath"] = md.path
        data["_filename"] = os.path.basename(md.path)
    for attr in attributes:
        try:
            value = md.get(attr)
            attr_type = get_attribute_type(attr)
            if json_ and attr_type in ["list", "list[datetime.datetime]"]:
                # preserve lists for json output and convert datetimes if needed
                if attr_type == "list[datetime.datetime]":
                    # value could be 'None' if attribute not set
                    value = [v.isoformat() for v in value] if value else []
            else:
                value = value_to_str(value)
        except Exception as e:
            return f"Error loading attribute {attr}: {e}"
        else:
            try:
                name, short_name = get_attribute_names(attr)
            except ValueError:
                return f"UNKNOWN ATTRIBUTE {attr}: THIS ATTRIBUTE NOT HANDLED"
            else:
                if json_:
                    data[name] = value
                else:
                    click.echo(
                        f"{short_name:{_SHORT_NAME_WIDTH}}{name:{_LONG_NAME_WIDTH}} = {value}"
                    )
    if json_:
        json_str = json.dumps(data)
        click.echo(json_str)


def validate_mirror_attributes_with_error(mirror: t.Tuple[t.Tuple[str, str]]):
    """Validate mirror attributes"""
    for item in mirror:
        attr1, attr2 = item

        validate_attribute_names((attr1, attr2))
        attr1 = get_attribute_name(attr1)
        attr2 = get_attribute_name(attr2)

        # avoid self mirroring
        if attr1 == attr2:
            return f"cannot mirror the same attribute: {attr1} {attr2}"

        # check type compatibility
        if get_attribute_type(attr1) != get_attribute_type(attr2):
            # can only mirror compatible attributes
            return f"Cannot mirror {attr1}, {attr2}: incompatible types"

    return None


def md_backup_metadata(filepath: str, backup_file: str, verbose: bool):
    """Backup metadata from file

    Args:
        filepath: path to file
        backup_file: path to backup file
        verbose: if True, print verbose output
    """
    # TODO: this is ripe for refactoring with a sqlite database
    # Currently, the code writes the entire backup database each time a file is processed
    if verbose:
        click.echo(f"  Backing up attribute data for {filepath}")
    # load the file if it exists, merge new data, then write out the file again
    backup_data = load_backup_file(backup_file) if backup_file.is_file() else {}
    backup_dict = get_backup_dict(filepath)
    backup_data[pathlib.Path(filepath).name] = backup_dict
    write_backup_file(backup_file, backup_data)


def md_restore_metadata(filepath: str, backup_file: str, verbose: bool):
    """Restore metadata from backup file

    Args:
        filepath: path to file to restore metadata for
        backup_file: path to backup file
        verbose: if True, print verbose output
    """

    try:
        backup_data = load_backup_file(backup_file)
        attr_dict = backup_data[pathlib.Path(filepath).name]
        if verbose:
            click.echo(f"  Restoring attribute data for {filepath}")
        md = OSXMetaData(filepath)
        for attr, value in attr_dict.items():
            if attr not in WRITABLE_ATTRIBUTES:
                continue
            if not value:
                # TODO: should values be set to None on restore if they were None in the backup?
                continue
            attr_type = get_attribute_type(attr)
            if attr in _TAGS_NAMES:
                value = [Tag(v[0], v[1]) for v in value]
            if attr_type == "datetime.datetime":
                value = datetime.datetime.fromisoformat(value)
            elif attr_type == "list[datetime.datetime]":
                value = [datetime.datetime.fromisoformat(v) for v in value]
            md.set(attr, value)
    except FileNotFoundError:
        click.echo(
            f"Missing backup file {backup_file} for {filepath}, skipping restore",
            err=True,
        )
    except KeyError:
        if verbose:
            click.echo(f"  Skipping restore for file {filepath}: not in backup file")


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

        # add findercolor which isn't a standard kMDx item
        attr_tuples.append(
            (
                "findercolor",
                "findercolor; Finder color tag value. "
                + "The value can be either a number or the name of the color as follows: "
                + f"{', '.join([f'{colorid}: {color}' for color, colorid in _COLORNAMES_LOWER.items() if colorid != FINDER_COLOR_NONE])}; "
                + "integer or string.",
            )
        )
        attr_tuples = sorted(attr_tuples)

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
            + "restore, wipe, copyfrom, clear, set, append, remove, mirror, get, list, backup.  "
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
            + "See also findercolor."
        )
        formatter.write("\n")

        formatter.write_dl(attr_tuples)
        help_text += formatter.getvalue()
        return help_text


# All the command line options defined here
FILES_ARGUMENT = click.argument(
    "files", metavar="FILE", nargs=-1, type=click.Path(exists=True), required=True
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
    help="Set ATTRIBUTE to VALUE. "
    "If ATTRIBUTE is a multi-value attribute, such as keywords (kMDItemKeywords), "
    "you may specify --set multiple times to add to the array of values: "
    "'--set keywords foo --set keywords bar' will set keywords to ['foo', 'bar']. "
    "Not that this will overwrite any existing values for the attribute; see also --append.",
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
    help="Append VALUE to ATTRIBUTE; for multi-valued attributes, appends only if VALUE is not already present. "
    "May be used in combination with --set to add to an existing value: "
    "'--set keywords foo --append keywords bar' will set keywords to ['foo', 'bar'], "
    "overwriting any existing values for the attribute.",
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
    mirror,
    backup,
    restore,
    verbose,
    copyfrom,
    files_only,
    pattern,
):
    """Read/write metadata from file(s)."""

    if debug:
        logging.disable(logging.NOTSET)

    # validate values for --set, --clear, --append, --get, --remove
    for attributes in [set_, append, remove, clear, get]:
        try:
            validate_attribute_names(attributes)
        except click.BadParameter as e:
            click.echo(e)
            ctx.exit(1)

    # check compatible types for mirror
    if mirror:
        if error := validate_mirror_attributes_with_error(mirror):
            click.echo(error, err=True)
            ctx.exit(1)

    # check that json_ only used with get or list_
    if json_ and not any([get, list_]):
        click.echo("--json can only be used with --get or --list", err=True)
        # click.echo("")  # add a new line before rest of help text
        # click.echo(ctx.get_help())
        ctx.exit(1)

    # can't backup and restore at once
    if backup and restore:
        click.echo("--backup and --restore cannot be used together", err=True)
        # click.echo("")  # add a new line before rest of help text
        # click.echo(ctx.get_help())
        ctx.exit(1)

    # loop through each file, process it, then do backup or restore if needed
    for filename in files:
        if not all([os.path.isdir(filename), walk, pattern]):
            process_files(
                ctx,
                [filename],
                json_,
                set_,
                append,
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
                    files_only,
                )


def process_files(
    ctx,
    files,
    json_,
    set_,
    append,
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
    files_only,
):
    """process list of files, calls process_single_file to process each file
    options processed in this order: wipe, copyfrom, clear, set, append, remove, mirror, get, list
    Note: expects all attributes passed in parameters to be validated as valid attributes
    """
    for filename in files:
        fpath = pathlib.Path(filename).resolve()
        backup_file = pathlib.Path(pathlib.Path(filename).parent) / BACKUP_FILENAME

        if files_only and fpath.is_dir():
            if verbose:
                click.echo(f"Skipping directory: {fpath}")
            continue

        if verbose:
            click.echo(f"Processing file: {fpath}")

        if restore:
            md_restore_metadata(fpath, backup_file, verbose)

        process_single_file(
            ctx,
            fpath,
            json_,
            set_,
            append,
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
            md_backup_metadata(fpath, backup_file, verbose)


def process_single_file(
    ctx,
    fpath,
    json_,
    set_,
    append,
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
    Note: expects all attributes passed in parameters to be validated as valid attributes
    """

    md = OSXMetaData(fpath)

    if wipe:
        md_wipe_metadata(md, verbose)

    if copyfrom:
        # TODO: add option to clear existing attributes if copyfrom does not have them
        md_copyfrom_metadata(md, copyfrom, verbose)

    if clear:
        md_clear_metadata(md, fpath, clear, verbose)

    if set_:
        if error := md_set_metadata_with_error(md, set_, verbose):
            click.echo(error, err=True)
            ctx.exit(1)

    if append:
        if error := md_append_metadata_with_error(md, append, verbose):
            click.echo(error, err=True)
            ctx.exit(1)

    if remove:
        if error := md_remove_metadata_with_error(md, remove, verbose):
            click.echo(error, err=True)
            ctx.exit(1)

    if mirror:
        if error := md_mirror_metadata_with_error(md, mirror, verbose):
            click.echo(error, err=True)
            ctx.exit(1)

    if get:
        if error := md_get_metadata_with_error(md, get, json_):
            click.echo(error, err=True)
            ctx.exit(1)

    if list_:
        if error := md_list_metadata_with_error(md, json_):
            click.echo(error, err=True)
            ctx.exit(1)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
