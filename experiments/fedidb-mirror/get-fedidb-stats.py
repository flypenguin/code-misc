#!/usr/bin/env python3

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///

import requests
import json
import sqlite3
from argparse import ArgumentParser
from pathlib import Path

FEDIDB_SERVERS = "https://api.fedidb.org/v1/servers"
JSON_FILE = "fedidb-servers.json"
DB_FILE = "fedidb.sqlite3"


def download_servers():
    servers = []
    next_batch = FEDIDB_SERVERS
    idx = 0
    while next_batch:
        rsp = requests.get(next_batch, params={"limit": 40}).json()
        servers += rsp.get("data", [])
        next_batch = rsp.get("links", {}).get("next", "")
        idx += 1
        if idx > 0 and idx % 5 == 0:
            print(".", end="", flush=True)
    print()
    print(f"Done. Got {len(servers)} server datasets.")
    with open(JSON_FILE, "w") as outfile:
        outfile.write(json.dumps(servers, indent=2))


def create_db():
    db_file = Path(DB_FILE)
    if db_file.is_file():
        db_file.unlink()

    with open(JSON_FILE, "r") as infile:
        servers = json.loads(infile.read())

    servers = [
        (
            s["domain"],
            s["description"],
            s["location"]["city"],
            s["location"]["country"],
            s["stats"]["user_count"],
            s["stats"]["monthly_active_users"],
            s["stats"]["status_count"],
            s["open_registration"],
            s["software"].get("name"),
            s["software"].get("version"),
        )
        for s in servers
    ]

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute(
        "create table servers(domain, desc, city, country, num_users, "
        "num_mau, num_status, status_per_user, sw_name, sw_version, open)"
    )
    cur.executemany(
        "insert into servers (domain, desc, city, country, num_users, num_mau, "
        "num_status, open, sw_name, sw_version)"
        "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        servers,
    )
    con.commit()

    cur.execute(
        "update servers set status_per_user = round(cast(num_status as real) / num_users, 2);"
    )
    con.commit()

    con.close()


if __name__ == "__main__":
    parser = ArgumentParser()
    subs = parser.add_subparsers()

    sub_parser = subs.add_parser("download")
    sub_parser.set_defaults(func=download_servers)

    sub_parser = subs.add_parser("create-db")
    sub_parser.set_defaults(func=create_db)

    args = parser.parse_args()

    args.func()
