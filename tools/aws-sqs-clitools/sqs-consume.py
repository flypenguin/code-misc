#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime as dt
from functools import partial
from pathlib import Path
from typing import Annotated, Optional

import boto3
import typer
from environs import Env
from loguru import logger
from rich import print_json

cli = typer.Typer()
env = Env()

logger.remove()
logger.add(
    sys.stderr,
    level=env("LOGLEVEL", "INFO"),
    format="{level:<8} | {message}",
)

jdump = partial(json.dumps, indent=2, sort_keys=True)


def save_message(path, basename, content, suffix="txt"):
    with open(Path(path, basename + "." + suffix), "w") as outfile:
        outfile.write(content)


def print_message(
    message,
    msg_index,
    decode_json: bool,
    json_decode_path: Optional[str],
    save_path: Optional[Path] = None,
):
    ts_str = f"{dt.now().timestamp():.6f}"
    if decode_json:
        msg_dict = json.loads(message.body)
        if json_decode_path:
            if save_path:
                basename = f"{ts_str}.{msg_index:06}.0"
                save_message(save_path, basename, jdump(msg_dict), suffix="json")
            for idx, p in enumerate(json_decode_path.split(".")):
                msg_dict = json.loads(msg_dict[p])
                if save_path:
                    basename = f"{ts_str}.{msg_index:06}.{idx+1}-{p}"
                    save_message(save_path, basename, jdump(msg_dict), suffix="json")
        elif save_path:
            basename = f"{ts_str}.{msg_index:06}"
            save_message(save_path, basename, jdump(msg_dict), suffix="json")
        print_json(jdump(msg_dict))
    else:
        message_str = str(message.body)
        if save_path:
            basename = f"{ts_str}.{msg_index}"
            save_message(save_path, basename, message_str)
        print(message_str)


@cli.command()
def consume(
    queue_name: str,
    delete: Annotated[
        bool,
        typer.Option(help="deletes the message after receiving"),
    ] = True,
    continuous: Annotated[
        bool,
        typer.Option(
            "--continuous/--once", "-c/-1", help="keep consuming indefinitely"
        ),
    ] = True,
    decode_json: Annotated[
        bool,
        typer.Option("--json", "-j", help="decode the message as JSON"),
    ] = False,
    json_decode_path: Annotated[
        str,
        typer.Option(
            "--decode-path",
            "-p",
            help="applies json decodes recursively, requires --json",
        ),
    ] = "",
    drain: Annotated[
        bool,
        typer.Option(
            "-d",
            "--drain",
            help="drains all messages in the queue without printing anything",
        ),
    ] = False,
    aws_region: Annotated[
        str,
        typer.Option(help="use this SQS region"),
    ] = "eu-central-1",
    timeout_secs: Annotated[
        int,
        typer.Option("--timeout", help="the long-poll timeout to use"),
    ] = 10,
    save_path: Annotated[
        str,
        typer.Option("--save", "-s", help="save all messages unter this path"),
    ] = "",
):
    sqs = boto3.resource(
        "sqs",
        region_name=aws_region,
        # see here: https://github.com/boto/botocore/issues/2683
        endpoint_url=f"https://sqs.{aws_region}.amazonaws.com",
    )
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    logger.debug(f"found queue: {queue}")

    if drain:
        logger.warning(f"purging queue: {queue}")
        queue.purge()
        return

    jdp = json_decode_path
    dj = decode_json
    if save_path:
        sp = Path(save_path)
        try:
            os.makedirs(save_path)
        except FileExistsError:
            pass
    else:
        sp = None

    num_msgs = 0

    while True:
        messages = queue.receive_messages(
            MaxNumberOfMessages=1,
            WaitTimeSeconds=min(60, timeout_secs),
        )

        if messages:
            message = messages[0]
            logger.info(f"message_id={message.message_id} num={num_msgs}")
            print_message(message, num_msgs, dj, jdp, sp)
            if delete:
                message.delete()
                logger.debug(f"message deleted: {message.message_id}")

            num_msgs += 1

        if not continuous:
            break


if __name__ == "__main__":
    cli()
