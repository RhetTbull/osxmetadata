# /usr/bin/env python

import osxmetadata
import argparse
import sys
import os.path
import os
from pathlib import Path
import json

# TODO: add md5 option
# TODO: how is metadata on symlink handled?
# should symlink be resolved before gathering metadata?
# currently, symlinks are resolved before handling metadata but not sure this is the right behavior
# in 10.13.6: synlinks appear to inherit tags but not Finder Comments:
#   e.g. changes to tags in a file changes tags in the symlink but symlink can have it's own finder comment
#   Finder aliases inherit neither
# TODO: add selective restore (e.g only restore files matching command line path)
#   e.g osxmetadata -r meta.json *.pdf

# curstom error handler
def onError(e):
    tqdm.write(str(e) + "\n", file=sys.stderr)
    return e


# custom argparse class to show help if error triggered
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


def process_arguments():
    parser = MyParser(
        description="Import and export metadata from files", add_help=False
    )

    # parser.add_argument(
    #     "--test",
    #     action="store_true",
    #     default=False,
    #     help="Test mode: do not actually modify any files or metadata"
    #     + "most useful with --verbose",
    # )

    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        default=False,
        help="Show this help message",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Print verbose output during processing",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        default=False,
        help="Output to JSON, optionally provide output file name: --outfile=file.json  "
        + "NOTE: if processing multiple files each JSON object is written to a new line as a separate object (ie. not a list of objects)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help="Be extra quiet when running.",
    )

    # parser.add_argument(
    #     "--noprogress",
    #     action="store_true",
    #     default=False,
    #     help="Disable the progress bar while running",
    # )

    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Force new metadata to be written even if unchanged",
    )

    parser.add_argument(
        "-o",
        "--outfile",
        help="Name of output file.  If not specified, output goes to STDOUT",
    )

    parser.add_argument(
        "-r",
        "--restore",
        help="Restore all metadata by reading from JSON file RESTORE (previously created with --json --outfile=RESTORE). "
        + "Will overwrite all existing metadata with the metadata specified in the restore file. "
        + "NOTE: JSON file expected to have one object per line as written by --json",
    )

    parser.add_argument(
        "--addtag",
        action="append",
        help="add tag/keyword for file. To add multiple tags, use multiple --addtag otions. e.g. --addtag foo --addtag bar",
    )

    parser.add_argument(
        "--cleartags",
        action="store_true",
        default=False,
        help="remove all tags from file",
    )

    parser.add_argument("--rmtag", action="append", help="remove tag from file")

    parser.add_argument("--setfc", help="set Finder comment")

    parser.add_argument(
        "--clearfc", action="store_true", default=False, help="clear Finder comment"
    )

    parser.add_argument(
        "--addfc",
        action="append",
        help="append a Finder comment, preserving existing comment",
    )

    # parser.add_argument(
    #     "--list",
    #     action="store_true",
    #     default=False,
    #     help="List all tags found in Yep; does not update any files",
    # )

    parser.add_argument("files", nargs="*")

    args = parser.parse_args()
    # if no args, show help and exit
    if len(sys.argv) == 1 or args.help:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return args


def process_file(fpath, fp, args={}):
    try:
        data = get_set_metadata(fpath, args)
        if args.json:
            write_json_data(fp, data)
        else:
            write_text_data(fp, data)

    except (IOError, OSError, ValueError):
        # data[str(fpath)] = None
        print(f"warning: error processing metadata for {fpath}", file=sys.stderr)


def process_files(files=[], fp=sys.stdout, quiet=False, verbose=False, args={}):
    # use os.walk to walk through files and collect metadata
    # on each file
    # symlinks can resolve to missing files (e.g. unmounted volume)
    # so catch those errors and set data to None
    # osxmetadata raises ValueError if specified file is missing

    for f in files:
        if os.path.isdir(f):
            for root, dirname, filenames in os.walk(f):
                if args.verbose:
                    print(f"Processing {root}")
                for fname in filenames:
                    fpath = Path(f"{root}/{fname}").resolve()
                    process_file(fpath, fp, args)
        else:
            fpath = Path(f).resolve()
            process_file(fpath, fp, args)


# sets metadata based on args then returns dict with all metadata on the file
def get_set_metadata(fname, args={}):
    try:
        md = osxmetadata.OSXMetaData(fname)

        # clear tags
        if args.cleartags:
            md.tags.clear()

        # remove tags
        if args.rmtag:
            tags = md.tags
            for t in args.rmtag:
                if t in tags:
                    md.tags.remove(t)

        # update tags
        if args.addtag:
            new_tags = []
            new_tags += args.addtag
            old_tags = md.tags
            tags_different = (sorted(new_tags) != sorted(old_tags)) or args.force
            if tags_different:
                md.tags.update(*new_tags)

        # finder comments
        if args.clearfc:
            md.finder_comment = ""

        if args.addfc:
            for fc in args.addfc:
                md.finder_comment += fc

        if args.setfc:
            old_comment = md.finder_comment
            if (old_comment != args.setfc) or args.force:
                md.finder_comment = args.setfc

        tags = list(md.tags)
        fc = md.finder_comment
        dldate = md.download_date
        dldate = str(dldate) if dldate is not None else None
        where_from = md.where_from
        data = {
            "file": str(fname),
            "tags": tags,
            "fc": fc,
            "dldate": dldate,
            "where_from": where_from,
        }
    except (IOError, OSError) as e:
        return onError(e)
    return data


# sets metadata based on data dict as returned by get_set_metadata or restore_from_json
# clears any existing metadata
def set_metadata(data, quiet=False):
    try:
        md = osxmetadata.OSXMetaData(data["file"])

        md.tags.clear()
        if data["tags"]:
            if not quiet:
                print(f"Tags: {data['tags']}")
            md.tags.update(*data["tags"])

        md.finder_comment = ""
        if data["fc"]:
            if not quiet:
                print(f"Finder comment: {data['fc']}")
            md.finder_comment = data["fc"]

        # tags = list(md.tags)
        # fc = md.finder_comment
        # dldate = md.download_date
        # dldate = str(dldate) if dldate is not None else None
        # where_from = md.where_from
        # data = {
        #     "file": str(fname),
        #     "tags": tags,
        #     "fc": fc,
        #     "dldate": dldate,
        #     "where_from": where_from,
        # }
    except (IOError, OSError) as e:
        return onError(e)
    return data


def write_json_data(fp, data):
    json.dump(data, fp)
    fp.write("\n")


def write_text_data(fp, data):
    file = data["file"]

    fc = data["fc"]
    fc = fc if fc is not None else ""

    dldate = data["dldate"]
    dldate = dldate if dldate is not None else ""

    where_from = data["where_from"]
    where_from = where_from if where_from is not None else ""

    tags = data["tags"]
    tags = tags if len(tags) is not 0 else ""

    print(f"file: {file}", file=fp)
    print(f"tags: {tags}", file=fp)
    print(f"Finder comment: {fc}", file=fp)
    print(f"Download date: {dldate}", file=fp)
    print(f"Where from: {where_from}", file=fp)
    print("\n", file=fp)


def restore_from_json(json_file, quiet=False):
    fp = None
    try:
        fp = open(json_file, mode="r")
    except:
        print(f"Error opening file {json_file} for reading")
        sys.exit(2)

    for line in fp:
        data = json.loads(line)
        if not quiet:
            print(f"Restoring metadata for {data['file']}")
        set_metadata(data, quiet)


def main():
    args = process_arguments()

    if args.restore:
        if not args.quiet:
            print(f"Restoring metadata from file {args.restore}")
        restore_from_json(args.restore, args.quiet)

    elif args.files:
        output_file = args.outfile if args.outfile is not None else None
        fp = sys.stdout
        if output_file is not None:
            try:
                fp = open(output_file, mode="w+")
            except:
                print(f"Error opening file {output_file} for writing")
                sys.exit(2)

        process_files(
            files=args.files, quiet=args.quiet, verbose=args.verbose, args=args, fp=fp
        )

        if output_file is not None:
            fp.close()


if __name__ == "__main__":
    main()
