#!/usr/bin/env python3

"""
The leaked data from Facebook is a bit weird and non-uniform across the
leaked files. At least Switzerland, Netherlands & Germany can be "normalized"
using this script.

What you have is basically this:

4017112345678,1000011111111,Hans,Wurst,male,Berlin, Germany,Spandau,In a relationship,,7/14/2017 12,00,00 AM,,

In total there are 10 (!) fields (see below, but in a different order).
Unfortunately this is *invalid* CSV, cause the time stamp and the location
data has in itself non-escaped commas.

To parse this you have to apply a bit of logic, which is this script.

It will ...
    * parse the fields which are easily parsed
    * search for a time stamp and parse it using strptime() (this contains a
      FIXED number of invalid ","s)
    * now the only thing remaining is the location data which contains a
      VARIABLE number of invalid ","s, so this can be detected as well.
"""


import argparse
import csv
import datetime as dt
import glob
import os.path
import sys


config = None
date_format = "%m/%d/%Y %H,%M,%S %p"
headers_norm = [
    "tel",
    "fbid",
    "fname",
    "lname",
    "sex",
    "mstatus",
    "timestamp",
    "email",
    "birthdate",
    "location",
]
headers_skip = ["file", "lineno", "data"]


def process(filename, handle, outfile, skipfile, separator):
    global config
    add_headers = [x[0] for x in config.set]
    add_values = [x[1] for x in config.set]
    csv_norm = csv.writer(outfile)
    csv_skip = csv.writer(skipfile)
    csv_norm.writerow(add_headers + headers_norm)
    csv_skip.writerow(headers_skip)
    for idx, line in enumerate(handle):
        if idx == config.max:
            print(f"    line {idx}: max entries reached, stop file processing")
            break

        line = line.strip()
        # tel, id, fname, lname, sex, rest
        fields = line.split(separator, 5)

        # determine timestamp
        rest = fields.pop()
        if rest.find("00 AM") != -1:
            # we have a time stamp, easy
            fields2 = rest.split(separator)
            # marital_status, employer
            fields += fields2[-7:-6]
            # date
            fields.append(",".join(fields2[-5:-2]))
            # email, birthdate(?)
            fields += fields2[-2:]
            # place
            fields.append(",".join(fields2[:-7]).strip(" ,"))
        else:
            print(f"    line {idx}: skipped: ", line)
            csv_skip.writerow([filename, idx, line])
            continue

        if len(fields) != 10:
            print(f"    line {idx}: wrong # of fields: {fields})")
            csv_skip.writerow([filename, idx, line])
            continue

        # convert timestamp
        fields[6] = dt.datetime.strptime(fields[6], date_format).isoformat()

        if config.print:
            print(fields)

        csv_norm.writerow(add_values + fields)


def detect_separator(infile):
    skip_lines = 10
    check_lines = 100
    desired_average = 14
    separators = [",", ":", "-", ";", "&"]
    tmp = [next(infile) for _ in range(skip_lines)]
    lines = [next(infile) for _ in range(check_lines)]
    averages = []
    for sep in separators:
        lengths = [len(s.split(sep)) for s in lines]
        averages.append((sep, sum(lengths) / check_lines))
    import pprint

    sep, val = sorted(averages, key=lambda x: x[1])[-1]
    if abs(val - desired_average) > 2:
        print("ERROR: unable to determine field separator")
        sys.exit(-1)
    return sep


def iterate():
    global config
    for filename in glob.glob(config.glob):
        src_dir = os.path.dirname(filename)
        src_full = os.path.basename(filename)
        tgt_dir = config.directory if config.directory else src_dir
        src_file, src_ext = os.path.splitext(src_full)
        # prevent our own files being processed
        if (
            src_full.endswith(".normalized.csv")
            or src_file.endswith(".skipped")
            or src_ext.endswith(".skipped")
        ):
            print(f"Skipping {filename}.")
            continue
        tgt_file = os.path.join(tgt_dir, src_file + ".normalized.csv")
        tgt_skip = os.path.join(tgt_dir, src_file + ".skipped" + src_ext)
        print(f"Processing {filename} ...")
        if config.separator == "auto":
            with open(filename, "r", encoding=config.encoding) as infile:
                sep = detect_separator(infile)
                print(f"    found separator '{sep}'")
        else:
            sep = config.separator
        with open(filename, "r", encoding=config.encoding) as infile, open(
            tgt_file, "w"
        ) as outfile, open(tgt_skip, "w") as skipfile:
            process(filename, infile, outfile, skipfile, separator=sep)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("glob")
    parser.add_argument(
        "-s",
        "--separator",
        default="auto",
        help="Configure column separator",
    )
    parser.add_argument(
        "-d",
        "--directory",
        default=None,
        help="Set output directory",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        help="Set additional fields",
    )
    parser.add_argument(
        "-m",
        "--max",
        default=-1,
        type=int,
        help="Stop after this many entries per file",
    )
    parser.add_argument(
        "--print",
        default=False,
        action="store_true",
        help="Print extracted fields (please use with --max)",
    )
    parser.add_argument(
        # https://stackoverflow.com/a/33294156/902327
        "-e",
        "--encoding",
        default="utf-8",
        help="Source file encoding, use 'utf-8-sig' for files with BOM",
    )
    config = parser.parse_args()
    config.set = [tuple(x.split("=", 1)) for x in config.set]
    iterate()
