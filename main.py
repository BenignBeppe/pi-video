#! /usr/bin/env python

import os
import logging
# import getpass
import sqlite3
import subprocess
from time import sleep

from flask import Flask
from flask import request
from flask import jsonify
from flask import abort
from flask_cors import CORS
# from omxplayer.player import OMXPlayer
import youtube_dl

# from omx_player import OmxPlayer
from vlc_player import VlcPlayer

app = Flask(__name__)
CORS(app)
media_player = None
omxplayer = None
url = ""
database_connection = None
player = VlcPlayer()

def setup_database():
    execute_database(
        "CREATE TABLE IF NOT EXISTS session (url text, time real)"
    )
    execute_database(
        "CREATE TABLE IF NOT EXISTS video_urls (player_url text, video_url text)"
    )

def execute_database(statement):
    logging.debug("SQLITE: {}".format(statement))
    cursor = database_connection.cursor()
    cursor.execute(statement)
    database_connection.commit()
    return cursor

# def setup_dbus():
#     # try:
#         user = getpass.getuser()
#         omxplayer_dbus_address = "/tmp/omxplayerdbus.{}".format(user)
#         os.environ["DBUS_SESSION_BUS_ADDRESS"] = \
#             open(omxplayer_dbus_address).read().rstrip()
#         omxplayer_dbus_pid = "/tmp/omxplayerdbus.{}.pid".format(user)
#         os.environ["DBUS_SESSION_BUS_PID"] = \
#             open(omxplayer_dbus_pid).read().rstrip()
#         bus = dbus.SessionBus()
#         # FIXME
#         global media_player
#         media_player = bus.get_object(
#             "org.mpris.MediaPlayer2.omxplayer",
#             "/org/mpris/MediaPlayer2"
#         )
#         logging.debug("DBus setup properly.")
#     #     return True
#     # except:
#     #     logging.exception("Couldn't setup DBus.")
#     #     return False

def get_from_database(table, variable):
    cursor = execute_database("SELECT {} FROM {}".format(variable, table))
    return cursor.fetchall()[-1]

@app.route("/video/play_pause", methods=["POST"])
def play_pause():
    player.play_pause()
    playing = player.get_playing()
    save_session()
    return jsonify(playing=playing), 200

@app.route("/video/back", methods=["POST"])
def back():
    duration = float(get_query_argument("duration"))
    time = player.seek(-duration)
    save_session()
    return jsonify(time=time), 200

def get_query_argument(key):
    return request.form.get(key)

def save_session():
    time = player.get_time()
    logging.info("Saving session: {}, {}".format(url, time))
    execute_database(
        'REPLACE INTO session VALUES("{}", {})'.format(url, time)
    )

@app.route("/video/forward", methods=["POST"])
def forward():
    duration = float(get_query_argument("duration"))
    time = player.seek(duration)
    save_session()
    return jsonify(time=time), 200

@app.route("/video/status", methods=["GET"])
def status():
    # try:
    time = player.get_time()
    playing = player.get_playing()
    return jsonify(url=url, time=time, playing=playing), 200
    # except:
    #     abort(500)

@app.route("/video/skip", methods=["POST"])
def skip():
    hours = int(get_query_argument("hours"))
    minutes = int(get_query_argument("minutes"))
    seconds = int(get_query_argument("seconds"))
    seconds = hours * 60 * 60 + \
        minutes * 60 + \
        seconds
    time = player.skip(seconds)
    save_session()
    return jsonify(time=time), 200

@app.route("/video/duration")
def duration():
    duration = player.get_duration()
    if duration is None:
        abort(500)
    return jsonify(duration=duration), 200

@app.route("/video/load", methods=["POST"])
def load(get_fresh_url=False):
    # try:
    #     stop()
    # except:
    #     logging.debug("Nothing to stop.")
    # FIXME
    global url
    video_url = None
    from_database = False
    url = get_query_argument("url")
    logging.info("Loading video from URL: {}".format(url))
    if not get_fresh_url:
        result = execute_database(
            'SELECT video_url FROM video_urls WHERE player_url="{}"'.format(url)
        ).fetchall()
        if result:
            video_url = result[0][0]
            if video_url:
                from_database = True
                logging.info("Using video URL from database: {}".format(video_url))
    if not video_url:
        logging.info("URL not found in database, fetching new.")
        ydl_opts = {
            "format": "[tbr<2500]",
            "forceurl": True
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info["url"]
            logging.info("Saving video URL to database.")
            execute_database(
                'REPLACE INTO video_urls VALUES("{}", "{}")'.format(url, video_url)
            )

    try:
        player.load(video_url)
    except:
        logging.info("Failed to load video.")
        if from_database:
            load(True)
    duration = player.get_duration()
    logging.debug("duration = {}".format(duration))
    save_session()
    return jsonify(duration=duration), 200

def call_command(command, output=False):
    if output:
        return subprocess.check_output(command).decode("utf-8")
    else:
        subprocess.Popen(command)


if __name__ == "__main__":
    log_path = "logs/video-server.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s %(message)s"
    )
    # setup_dbus()
    # while not setup_dbus(): sleep(1.0)
    database_connection = sqlite3.connect(
        "session.db",
        check_same_thread=False
    )
    setup_database()
    url = get_from_database("session", "url")
    logging.debug("Good to go.")
    app.run(host="0.0.0.0", debug=True)
    database_connection.close()
