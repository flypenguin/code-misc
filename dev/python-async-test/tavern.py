#!/usr/bin/env python

from flask import Flask

from time import sleep


wench = Flask(__name__)

waitfor = 1


@wench.route("/")
def index():
    return "Hello stranger!"


@wench.route("/arrr")
def wait():
    print("We have stew. Let me tell the cook you want some.")
    sleep(waitfor)
    print("Here you go :)")
    return "You get fed after {} seconds".format(waitfor)


@wench.route("/whisky")
def whisky():
    return "Hard drinks for hard men, eh?"


if __name__ == '__main__':
    wench.run(threaded=True)
