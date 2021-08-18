#!/usr/bin/env python3

import sys
import os
from argparse import ArgumentParser

from azure.servicebus import ServiceBusClient, ServiceBusMessage


SB_CONNSTR = os.environ["AZURE_SB_CONNECTION_STRING"]
SB_TOPIC = os.environ["AZURE_SB_TOPIC"]
SB_TOPIC_SUBSCRIPTION = os.environ["AZURE_SB_TOPIC_SUBSCRIPTION"]

config = None


def send_servicebus_message(message):
    sbc = ServiceBusClient.from_connection_string(
        SB_CONNSTR, logging_enable=config.verbose
    )
    sender = sbc.get_topic_sender(
        topic_name=SB_TOPIC,
    )
    msg = ServiceBusMessage(message)
    sender.send_messages(msg)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-s", "--stdin", action="store_true", default=False, help="read from stdin"
    )
    parser.add_argument("-f", "--file", help="read from file")
    parser.add_argument("-t", "--text", help="send text from command line")
    parser.add_argument(
        "-v", "--verbose", action="store_true", default=False, help="be more verbose"
    )
    config = parser.parse_args()

    if config.verbose:
        print(f"SB_CONNSTR={SB_CONNSTR}")
        print(f"SB_TOPIC={SB_TOPIC}")
        print(f"SB_TOPIC_SUBSCRIPTION={SB_TOPIC_SUBSCRIPTION}")

    if config.stdin:
        send_servicebus_message(sys.stdin.readlines())
    elif config.file:
        with open(config.file, "r") as infile:
            send_servicebus_message(infile.read())
    elif config.text:
        send_servicebus_message(config.text)
    else:
        print("Please choose one of -s/-f/-t !", file=sys.stderr)
        sys.exit(-1)
