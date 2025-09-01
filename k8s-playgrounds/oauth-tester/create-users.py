#!/usr/bin/env uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "bcrypt",
#     "pyyaml",
# ]
# ///

import base64
import csv
import hashlib
import os
import yaml
from argparse import ArgumentParser


SALT_LEN = 16
N = 2**14  # cost
R = 8  # block size
P = 1  # parallelization
DKLEN = 64  # length of derived key


def get_hash(password: str) -> str:
    pw_bytes = password.encode()  # str → bytes
    salt = os.urandom(SALT_LEN)
    key = hashlib.scrypt(pw_bytes, salt=salt, n=N, r=R, p=P, dklen=DKLEN)

    # Encode salt and key in URL-safe base64
    salt_b64 = base64.urlsafe_b64encode(salt).decode().rstrip("=")
    key_b64 = base64.urlsafe_b64encode(key).decode().rstrip("=")

    # Construct a string similar to the Argon2 format
    return f"$scrypt$ln={N.bit_length() - 1},r={R},p={P}${salt_b64}${key_b64}"


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
                "password": get_hash(plaintext_password.strip()),
            }

        print(yaml.dump({"users": users}, indent=2))
