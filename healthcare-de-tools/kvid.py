#!/usr/bin/env python3

# generates a "valid" german person's number ("krankenversichertennummer")
# as defined in wikipedia:
# https://de.wikipedia.org/wiki/Krankenversichertennummer

from random import randint
from argparse import ArgumentParser


config = None
int_a = ord("A")
int_0 = ord("0")


def gen_checksum(kvnr: str) -> int:
    assert len(kvnr) == 9
    # convert "E12..." to "0512..." ("E" -> "05")
    int_0 = ord("0")
    letter_code = ord(kvnr[0]) - ord("A") + 1  # 1, 2, ... 26
    converted_str = f"{letter_code:02}{kvnr[1:]}"
    # calculate checksum
    sum = 0
    # iterate over (index, val) with val = (0 .. 9)
    for i, val in enumerate(map(lambda x: ord(x) - int_0, converted_str)):
        # every 2nd iteration is multiplied by 2
        if i % 2:
            val *= 2
        # the sum of all digits of a number between 0..18: sum_dig = num - 9
        if val > 9:
            val -= 9
        sum += val
    return sum % 10


def gen() -> str:
    kvnr = []
    kvnr.append(chr(int_a + randint(0, 25)))
    for _ in range(8):
        kvnr.append(chr(int_0 + randint(0, 9)))
    kvnr_str = "".join(kvnr)
    kvnr_str += chr(int_0 + gen_checksum(kvnr_str))
    return kvnr_str


if __name__ == "__main__":
    parser = ArgumentParser()
    sps = parser.add_subparsers(help="Sub-command help", dest="cmd")

    sp = sps.add_parser("gen", help="Generate KV ID")
    sp = sps.add_parser("val", help="Validate KV ID")
    sp.add_argument("kv_id", help="The KV ID to validate")
    config = parser.parse_args()

    if config.cmd == "gen":
        print(gen())
    else:
        check_me = config.kv_id[:-1]
        check_should = gen_checksum(check_me)
        check_is = ord(config.kv_id[-1]) - int_0
        if check_is == check_should:
            print("KV ID valid.")
        else:
            print(
                f"Invalid KV ID. Checksum should be '{check_should}', is: '{check_is}'"
            )
