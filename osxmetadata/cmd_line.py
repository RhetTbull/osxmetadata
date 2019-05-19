# /usr/bin/env python

import osxmetadata
import argparse
import sys
import os.path
import os
from pathlib import Path
import json
from tqdm import tqdm

# TODO: add md5 option
# TODO: how is metadata on symlink handled?

# custom argparse class to show help if error triggered
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


def onError(e):
    sys.stderr.write(str(e) + "\n")


def process_arguments():
    parser = MyParser(
        description="Import and export metadata from files", add_help=False
    )

    parser.add_argument(
        "--test",
        action="store_true",
        default=False,
        help="Test mode: do not actually modify any files or metadata"
        + "most useful with --verbose",
    )
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
        help="Output to JSON, optionally provide output file name: --file=file.json",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help="Be extra quiet when running.",
    )

    parser.add_argument(
        "--noprogress",
        action="store_true",
        default=False,
        help="Disable the progress bar while running",
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


# simple progress spinner for use while
# analyzing file tree
# rolled my own to avoid importing another library
# using tqdm for progress bar but it lacks a spinner
# TODO: this could use an async/threaded implementation to slow it down
# but good enough for now
def create_progress_spinner():
    def spinning_cursor():
        while True:
            for cursor in "|/-\\":
                yield cursor

    spinner = spinning_cursor()
    return spinner


def update_progress_spinner(spinner):
    sys.stderr.write(next(spinner))
    sys.stderr.flush()
    sys.stderr.write("\b")


def process_files(files=[], noprogress=False, quiet=False, verbose=False):
    # use os.walk to walk through files and collect metadata
    # on each file
    # symlinks can resolve to missing files (e.g. unmounted volume)
    # so catch those errors and set data to None
    # osxmetadata raises ValueError if specified file is missing

    data = {}
    paths = []
    spinner = create_progress_spinner()
    # collect list of file paths to process
    if not quiet:
        print("Collecting files to process", file=sys.stderr)
    for f in files:
        if os.path.isdir(f):
            for root, dirname, filenames in os.walk(f):
                for fname in filenames:
                    if not noprogress:
                        update_progress_spinner(spinner)
                    fpath = Path(f"{root}/{fname}").resolve()
                    paths.append(fpath)
        else:
            if not noprogress:
                update_progress_spinner(spinner)
            fpath = Path(f).resolve()
            paths.append(fpath)

    # process each file path collected above
    # showprogress = True/False to enable/disable progress bar
    numfiles = len(paths)
    if not quiet:
        print(f"processing {numfiles} files", file=sys.stderr)
    for fpath in tqdm(iterable=paths, disable=noprogress):
        try:
            if verbose:
                tqdm.write(f"processing file {fpath}", file=sys.stderr)
            data[str(fpath)] = get_metadata(fpath)
        except ValueError:
            data[str(fpath)] = None
            tqdm.write(f"warning: error getting metadata for {fpath}", file=sys.stderr)

    return data


def get_metadata(fname):
    md = osxmetadata.OSXMetaData(fname)
    tags = list(md.tags)
    fc = md.finder_comment
    dldate = md.download_date
    dldate = str(dldate) if dldate is not None else None
    where_from = md.where_from
    data = {"tags": tags, "fc": fc, "dldate": dldate, "where_from": where_from}
    return data


def write_json_data(fname, data):
    print(json.dumps(data, indent=4))


def main():
    args = process_arguments()

    if args.files:
        data = process_files(
            files=args.files,
            noprogress=args.noprogress,
            quiet=args.quiet,
            verbose=args.verbose,
        )
        json_file = "test.json"
        write_json_data(json_file, data)


if __name__ == "__main__":
    main()
