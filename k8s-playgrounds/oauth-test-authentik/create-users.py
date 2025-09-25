#!/usr/bin/env uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "argon2-cffi",
#     "pyyaml",
# ]
# ///

import csv
import yaml
from argparse import ArgumentParser

from argon2 import PasswordHasher as ArgonHasher, Type


# class argon2.PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16, encoding='utf-8', type=Type.ID)


def argon2id_hash(
    password, time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16, encoding="utf-8", type_=Type.ID
):
    hasher = ArgonHasher(
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=hash_len,
        salt_len=salt_len,
        encoding=encoding,
        type=type_,
    )
    hash = hasher.hash(password)
    return hash


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("infile_csv")
    config = parser.parse_args()

    from pprint import pprint

    users = {}
    with open(config.infile_csv, "r") as infile:
        reader = csv.reader(infile)
        for row in reader:
            user_name, display_name, email_address, groups, plaintext_password = row
            if user_name.startswith("#"):
                continue
            users[user_name.strip().lower()] = {
                "disabled": False,
                "displayname": display_name.strip(),
                "email": email_address.strip().lower(),
                "groups": [g.strip() for g in groups.split(";")],
                "password": argon2id_hash(plaintext_password.strip()),
            }

        print(yaml.dump({"users": users}, indent=2))
