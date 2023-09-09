#!/usr/bin/env python3

import json
import sys
from datetime import datetime as dt
from functools import partial
from pathlib import Path
from typing import Annotated

import boto3
import typer
from environs import Env
from loguru import logger

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


@cli.command()
def produce(
    queue_name: str,
    msg: Annotated[str, typer.Option("-m", "--msg")] = None,
    msg_file: Annotated[typer.FileText, typer.Option("-f", "--file")] = None,
    aws_region: Annotated[str, typer.Option("-r", "--region")] = "eu-central-1",
):
    sqs = boto3.resource(
        "sqs",
        region_name=aws_region,
        # see here: https://github.com/boto/botocore/issues/2683
        endpoint_url=f"https://sqs.{aws_region}.amazonaws.com",
    )
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    logger.debug(f"found queue: {queue}")

    if msg:
        pass
    elif msg_file:
        msg = msg_file.read()
    else:
        msg = f"Test @ {dt()}"

    logger.debug(f"using message: {msg}")
    queue.send_message(MessageBody=msg)


if __name__ == "__main__":
    cli()
