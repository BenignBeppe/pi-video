#! /usr/bin/env python3

import os
import urllib
import json
import subprocess
import shlex
import time
import datetime
import logging
import getpass

from flask import Flask
from flask import request
from flask import jsonify
from flask import abort
from flask_cors import CORS
import dbus

app = Flask(__name__)
CORS(app)
media_player = None
omxplayer = None

def setup_dbus():
    try:
        user = getpass.getuser()
        omxplayer_dbus_address = "/tmp/omxplayerdbus.{}".format(user)
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = \
            open(omxplayer_dbus_address).read().rstrip()
        omxplayer_dbus_pid = "/tmp/omxplayerdbus.{}.pid".format(user)
        os.environ["DBUS_SESSION_BUS_PID"] = \
            open(omxplayer_dbus_pid).read().rstrip()
        bus = dbus.SessionBus()
        # FIXME
        global media_player
        media_player = bus.get_object(
            "org.mpris.MediaPlayer2.omxplayer",
            "/org/mpris/MediaPlayer2"
        )
        logging.debug("DBus setup properly.")
        return True
    except:
        logging.exception("Couldn't setup DBus.")
        return False

@app.route("/video/play_pause", methods=["POST"])
def pause():
    call_dbus("PlayPause")
    return "200"

def call_dbus(method_name, *args):
    if media_player is None:
        raise Exception("No media player DBus object.")
    try:
        logging.debug("Calling DBus method: {}{}".format(method_name, args))
        return media_player.get_dbus_method(method_name)(*args)
    except:
        raise Exception("Failed to call BDus method.")

@app.route("/video/back", methods=["POST"])
def back():
    duration = float(get_query_argument("duration"))
    seek(-duration)
    return ""

def get_query_argument(key):
    return request.form.get(key)

def seek(duration):
    microseconds = int(duration * 10 ** 6)
    call_dbus("Seek", dbus.Int64(microseconds))
    logging.debug("Seeked: {}".format(duration))

@app.route("/video/forward", methods=["POST"])
def forward():
    duration = float(get_query_argument("duration"))
    seek(duration)
    return ""

@app.route("/video/position", methods=["GET", "POST"])
def position():
    if request.method == "GET":
        try:
            microseconds = call_dbus("Position")
            position = microseconds / 10 ** 6
            return jsonify(position=position), 200
        except:
            abort(500)
    elif request.method == "POST":
        hours = int(get_query_argument("hours"))
        minutes = int(get_query_argument("minutes"))
        seconds = int(get_query_argument("seconds"))
        microseconds = hours * 60 * 60 * 1000000 + \
            minutes * 60 * 1000000 + \
            seconds * 1000000
        result = call_dbus(
            "SetPosition",
            dbus.ObjectPath("/not/used"),
            dbus.Int64(microseconds)
        )
        if result is None:
            abort(500)
        else:
            position = microseconds / 10 ** 6
            return jsonify(position=position), 200

@app.route("/video/duration")
def duration():
    duration = get_duration()
    if duration is None:
        abort(500)
    return jsonify(duration=duration), 200

def get_duration():
    microseconds = call_dbus("Duration")
    if microseconds is None:
        return None
    duration = microseconds / 10 ** 6
    return duration

@app.route("/video/load", methods=["POST"])
def load():
    try:
        stop()
    except:
        logging.debug("Nothing to stop.")
    url = get_query_argument("url")
    logging.debug("load(): {}".format(url))
    video_url = \
        call_command(["youtube-dl", "-g", "-f", "best", url], True).rstrip()
    command = ["omxplayer", "-o", "hdmi", video_url]
    logging.debug("Starting omxplayer: {}".format(command))
    omxplayer = call_command(command)
    while not setup_dbus(): time.sleep(1.0)
    duration = get_duration()
    return jsonify(duration=duration), 200

def stop():
    call_dbus("Quit")

def call_command(command, output=False):
    if output:
        return subprocess.check_output(command)
    else:
        subprocess.Popen(command)

if __name__ == "__main__":
    log_path = "logs/{}.log".format(datetime.datetime.now())
    logging.basicConfig(filename=log_path, level=logging.DEBUG)
    setup_dbus()
    logging.debug("Good to go.")
    app.run(host="0.0.0.0", debug=True)
