#!/usr/bin/env python3

import sys
import os
import datetime as dt
import json
from json.decoder import JSONDecodeError
from argparse import ArgumentParser
from pprint import pprint as pp

from azure.servicebus import ServiceBusClient, ServiceBusMessage


SB_CONNSTR = os.environ["AZURE_SB_CONNECTION_STRING"]
SB_TOPIC = os.environ["AZURE_SB_TOPIC"]
SB_TOPIC_SUBSCRIPTION = os.environ["AZURE_SB_TOPIC_SUBSCRIPTION"]

config = None


def run():
    # this is the essential part.
    sbc = ServiceBusClient.from_connection_string(SB_CONNSTR, logging=config.verbose)
    recv = sbc.get_subscription_receiver(
        topic_name=SB_TOPIC, subscription_name=SB_TOPIC_SUBSCRIPTION, max_wait_time=None
    )
    for msg in recv:
        if config.complete and config.mode == "PEEK_LOCK":
            recv.complete_message(msg)
        # until here.
        print(str(dt.datetime.now()), file=sys.stderr)
        try:
            # always try json decoding ...
            print(json.dumps(json.loads(str(msg)), indent=2, sort_keys=True))
        except JSONDecodeError:
            pp(str(msg))
        if not config.loop:
            print("breaking")
            break
        print("", file=sys.stderr)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-l", "--loop", action="store_true", default=False, help="don't stop receving"
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["PEEK_LOCK", "RECEIVE_AND_DELETE"],
        default="PEEK_LOCK",
        help="default PEEK_LOCK, see https://is.gd/3h8JEu",
    )
    parser.add_argument(
        "-c",
        "--complete",
        action="store_true",
        default=False,
        help="complete() message after getting it",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", default=False, help="be more verbose"
    )
    config = parser.parse_args()
    run()
