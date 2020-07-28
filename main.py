#! /usr/bin/env python3

import os
import urllib
import json
import subprocess
import shlex
from time import sleep
import datetime
import logging
import getpass
import sqlite3

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
url = ""
database_connection = None

def setup_database():
    execute_database(
        "CREATE TABLE IF NOT EXISTS session (url text, time real)"
    )

def execute_database(statement):
    logging.debug("SQLITE: {}".format(statement))
    cursor = database_connection.cursor()
    cursor.execute(statement)
    database_connection.commit()
    return cursor

def setup_dbus():
    # try:
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
    #     return True
    # except:
    #     logging.exception("Couldn't setup DBus.")
    #     return False

def get_from_database(variable):
    cursor = execute_database("SELECT {} FROM session".format(variable))
    return cursor.fetchall()[-1]

@app.route("/video/play_pause", methods=["POST"])
def play_pause():
    call_dbus("PlayPause")
    playing = get_playing()
    return jsonify(playing=playing), 200

def get_playing():
    status = call_dbus("PlaybackStatus")
    if status == "Playing":
        return True
    elif status == "Paused":
        return False
    logging.debug("ERROR: ", status)
    raise Exception("Unknown PlaybackStatus: '{}'".format(status))

def call_dbus(method_name, *args):
    setup_dbus()
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
    time = seek(-duration)
    return jsonify(time=time), 200

def get_query_argument(key):
    return request.form.get(key)

def seek(duration):
    microseconds = int(duration * 10 ** 6)
    call_dbus("Seek", dbus.Int64(microseconds))
    logging.debug("Seeked: {}".format(duration))
    time = get_time()
    save_session()
    return time

def save_session():
    time = get_time()
    logging.info("Saving session: {}, {}".format(url, time))
    execute_database(
        'REPLACE INTO session VALUES("{}", {})'.format(url, time)
    )

@app.route("/video/forward", methods=["POST"])
def forward():
    duration = float(get_query_argument("duration"))
    time = seek(duration)
    return jsonify(time=time), 200

@app.route("/video/status", methods=["GET"])
def status():
    try:
        time = get_time()
        playing = get_playing()
        return jsonify(url=url, time=time, playing=playing), 200
    except:
        abort(500)

def get_time():
    microseconds = call_dbus("Position")
    time = microseconds / 10 ** 6
    return time

@app.route("/video/time", methods=["POST"])
def time():
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
        time = get_time()
        save_session()
        return jsonify(time=time), 200

@app.route("/video/duration")
def duration():
    duration = get_duration()
    if duration is None:
        abort(500)
    return jsonify(duration=duration), 200

def get_duration():
    logging.debug("> get_duration()")
    microseconds = call_dbus("Duration")
    logging.debug(microseconds)
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
    # FIXME
    global url
    url = get_query_argument("url")
    logging.info("Loading video from URL: {}".format(url))
    youtube_dl_command = [
        "youtube-dl",
        "-g",
        "--no-playlist",
        "-f", "[tbr<2500]",
        url
    ]
    logging.debug("Calling youtube-dl: {}".format(" ".join(youtube_dl_command)))
    video_url = \
        call_command(youtube_dl_command, True).rstrip()
    omxplayer_command = ["omxplayer", "-o", "hdmi", video_url, "--no-boost-on-downmix"]
    logging.info("Starting omxplayer for URL: {}".format(video_url))
    logging.debug("Calling omxplayer: {}".format(" ".join(omxplayer_command)))
    omxplayer = call_command(omxplayer_command)
    # Wait until Omxplayer is done loading before returning duration.
    # while not setup_dbus(): sleep(1.0)
    logging.debug("Video loaded.")
    duration = get_duration()
    logging.debug("duration", duration)
    save_session()
    logging.debug(session)
    return jsonify(duration=duration), 200

def stop():
    call_dbus("Quit")

def call_command(command, output=False):
    if output:
        return subprocess.check_output(command).decode("utf-8")
    else:
        subprocess.Popen(command)


if __name__ == "__main__":
    log_path = "logs/video-server.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.DEBUG
    )
    # setup_dbus()
    # while not setup_dbus(): sleep(1.0)
    database_connection = sqlite3.connect(
        "session.db",
        check_same_thread=False
    )
    setup_database()
    url = get_from_database("url")
    logging.debug("Good to go.")
    app.run(host="0.0.0.0", debug=True)
    database_connection.close()
