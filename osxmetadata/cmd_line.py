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
# should symlink be resolved before gathering metadata?

# curstom error handler
def onError(e):
    tqdm.write(str(e) + "\n",file=sys.stderr)
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

    parser.add_argument("--addtag", action="append", help="add tags/keywords for file")
    
    parser.add_argument(
        "--cleartags",
        action="store_true",
        default=False,
        help="remove all tags from file",
    )

    parser.add_argument("--rmtag", action="append", help="remove tag from file")

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


def process_files(files=[], noprogress=False, quiet=False, verbose=False, args={}):
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
    if numfiles < 10:
        noprogress = True

    if not quiet:
        print(f"processing {numfiles} files", file=sys.stderr)
    for fpath in tqdm(iterable=paths, disable=noprogress):
        try:
            if verbose:
                tqdm.write(f"processing file {fpath}", file=sys.stderr)
            data[str(fpath)] = get_set_metadata(fpath,args)
        except (IOError, OSError, ValueError):
            # data[str(fpath)] = None
            tqdm.write(f"warning: error processing metadata for {fpath}", file=sys.stderr)

    return data


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
            tags_different = sorted(new_tags) != sorted(old_tags) or args.force
            if tags_different:
                md.tags.update(*new_tags)

        tags = list(md.tags)
        fc = md.finder_comment
        dldate = md.download_date
        dldate = str(dldate) if dldate is not None else None
        where_from = md.where_from
        data = {"tags": tags, "fc": fc, "dldate": dldate, "where_from": where_from}
    except (IOError, OSError) as e:
        return(onError(e))
    return data


def write_json_data(fname, data):
    if fname is None:
        print(json.dumps(data, indent=4))
    else:
        try:
            fp = open(fname, "w+")
            json.dump(data, fp, indent=4)
            fp.close()
        except:
            print(f"error writing to file {fname}", file=sys.stderr)


def write_text_data(fname, data):
    fp = sys.stdout
    if fname is not None:
        try:
            fp = open(fname, "w+")
        except:
            print(f"error opening file for writing {fname}", file=sys.stderr)

    for key in data:
        fc = data[key]["fc"]
        fc = fc if fc is not None else ""

        dldate = data[key]["dldate"]
        dldate = dldate if dldate is not None else ""

        where_from = data[key]["where_from"]
        where_from = where_from if where_from is not None else ""

        tags = data[key]["tags"]
        tags = tags if len(tags) is not 0 else ""

        print(f"{key}", file=fp)
        print(f"tags: {tags}", file=fp)
        print(f"Finder comment: {fc}", file=fp)
        print(f"Download date: {dldate}", file=fp)
        print(f"Where from: {where_from}", file=fp)
        print("\n", file=fp)

    if fname is not None:
        fp.close()


def main():
    args = process_arguments()

    if args.files:
        data = process_files(
            files=args.files,
            noprogress=args.noprogress,
            quiet=args.quiet,
            verbose=args.verbose,
            args = args,
        )

        output_file = args.outfile if args.outfile is not None else None
        
        if data:
            if args.json:
                write_json_data(output_file, data)
            else:
                write_text_data(output_file, data)


if __name__ == "__main__":
    main()
