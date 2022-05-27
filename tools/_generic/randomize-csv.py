#!/usr/bin/env python3

import csv
import re
from argparse import ArgumentParser
from collections import defaultdict
from random import shuffle
from pprint import pprint

config = None
limit = -1


def randomize():

    with open(config.srcfile, "r") as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        values = defaultdict(list)
        # read CSV into COLUMNS ...
        for rowcount, row in enumerate(reader):
            # print(row)
            for colname, val in zip(headers, row):
                values[colname].append(val)

            if rowcount == limit:
                break

        # shuffle columns
        for _, col in values.items():
            shuffle(col)

    # transpose columns into rows
    rows = zip(*[values[hd] for hd in headers])

    # overwrite old file with shuffled values
    with open(config.srcfile, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    parser = ArgumentParser(description="Randomize CSV files")
    parser.add_argument("srcfile", help="Which file to randomize")
    config = parser.parse_args()
    randomize()
