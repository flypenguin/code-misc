#!/usr/bin/env python

import uvloop
from sanic import Sanic
from sanic.response import text

from asyncio import set_event_loop_policy, sleep


set_event_loop_policy(uvloop.EventLoopPolicy())
sweetheart = Sanic(__name__)

waitfor = 1


@sweetheart.route("/")
async def index(*_):
    return text("Hey Baby!")


@sweetheart.route("/arrr")
async def wait(*_):
    print("Hello darling, I'll check if someone's available ...")
    await sleep(waitfor)
    print("All right sweetheart, the ladies are waiting for you :)")
    return text("Your get happy after {} seconds".format(waitfor))


@sweetheart.route("/whisky")
async def whisky(*_):
    return text("No drinks in here cowboy!")


if __name__ == '__main__':
    sweetheart.run(host="127.0.0.1", port=5100) #, debug=True)
