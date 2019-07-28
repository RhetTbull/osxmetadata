# /usr/bin/env python

import osxmetadata
import argparse
import sys

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

    # parser.add_argument(
    #     "-q",
    #     "--quiet",
    #     action="store_true",
    #     default=False,
    #     help="Be extra quiet when running.",
    # )

    # parser.add_argument(
    #     "--noprogress",
    #     action="store_true",
    #     default=False,
    #     help="Disable the progress bar while running",
    # )

    # parser.add_argument(
    #     "--list",
    #     action="store_true",
    #     default=False,
    #     help="List all tags found in Yep; does not update any files",
    # )

    parser.add_argument("files", nargs="*")

    args = parser.parse_args()
    # if no args, show help and exit
    if args.help:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return args


def main():
    args = process_arguments()
    if args.verbose:
        print("hello")

    if args.files:
        print(args.files)


if __name__ == "__main__":
    main()
