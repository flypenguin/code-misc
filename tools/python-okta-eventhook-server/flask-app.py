#!/usr/bin/env python

from flask import Flask
from flask import request

from flask.views import View

from json import dumps
from time import time
from datetime import datetime as dt
from os import mkdir
from os.path import join


app = Flask(__name__)
timestamp = dt.now().strftime("%Y-%m-%d_%H.%M.%S")
dirname = f"events-{timestamp}"
counter = 0


@app.route("/health", methods=["GET"])
def get_health():
    return "OK", 200


@app.route("/", methods=["GET"])
def get_verify():
    header_value = request.headers.get("X-Okta-Verification-Challenge", "nope")
    rv = {"verification": header_value}
    print("Verification: ", rv)
    return rv, 200


@app.route("/", methods=["POST"])
def post_event():
    global counter
    json = request.get_json()
    if json:
        with open(join(dirname, f"{counter}"), "w") as outfile:
            outfile.write(dumps(json, indent=2))
        counter += 1
    return "", 200


if __name__ == "__main__":
    mkdir(dirname)
    app.run()
