import logging
from time import sleep
import json

from flask import jsonify
from flask import render_template
from flask import request
from flask import abort
from flask import Response
from vlc import Instance
from youtube_dl import YoutubeDL

from app import app


SHORT_SKIP = 10
LONG_SKIP = 60


class Player:
    def __init__(self):
        self._instance = Instance()
        self._player = self._instance.media_player_new()
        self.page_url = None
        self.video_url = None


    def load(self, page_url):
        logging.info(f"Loading video from {page_url}.")
        self.page_url = page_url
        ydl_opts = {
            "format": "[tbr<2500]",
            "forceurl": True
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(page_url, download=False)
            video_url = info["url"]

        self.video_url = video_url
        logging.debug(f"Video URL: {video_url}.")
        media = self._instance.media_new(video_url)
        media.parse()
        self._player.set_media(media)
        logging.info("Starting playback.")
        self._player.play()


    def seek(self, amount):
        time = self.get_time()
        if time == None:
            return

        new_time = time + amount
        self.skip_to(new_time)
        return new_time


    def skip_to(self, time):
        self._player.set_time(int(time * 1000))


    def play_pause(self):
        self._player.pause()


    def get_duration(self):
        duration = self._player.get_length()
        if duration == -1:
            return 0

        return duration / 1000


    def get_time(self):
        time = self._player.get_time()
        if time == -1:
            return 0

        return time / 1000


    def get_playing(self):
        return self._player.is_playing() == 1


    def get_duration_string(self):
        return self._make_time_string(self.get_duration())


    def _make_time_string(self, seconds):
        """Convert second into string of the format 'H:MM:SS:'"""

        seconds = int(seconds)
        if seconds >= 60 * 60:
            hours = seconds // (60 * 60)
            seconds -= hours * (60 * 60)
        else:
            hours = 0
        if seconds >= 60:
            minutes = seconds // 60
            seconds -= minutes * 60
        else:
            minutes = 0
        time_string = f"{hours}:{minutes:02}:{seconds:02}"

        return time_string


    def get_time_string(self):
        return self._make_time_string(self.get_time())


player = Player()


@app.route("/")
def home():
    time = player.get_time()
    duration = player.get_duration()
    if duration:
        progress = time / duration * 100
    else:
        progress = 0
    page_url = player.page_url
    if page_url is None:
        page_url = ""
    time_string = player.get_time_string()
    duration_string = player.get_duration_string()
    parameters = {
        "time": time_string,
        "duration": duration_string,
        "progress": progress,
        "video_url": page_url
    }
    return render_template("player.html", **parameters)


@app.route("/load", methods=["POST"])
def load():
    page_url = request.form.get("url")
    if not page_url:
        abort(400, description="Missing required parameter 'url'.")

    player.load(page_url)
    return jsonify(duration=player.get_duration())


@app.route("/play-pause", methods=["POST"])
def play_pause():
    player.play_pause()
    return "", 200


@app.route("/skip-back-long", methods=["POST"])
def skip_back_long():
    player.seek(LONG_SKIP * -1)
    return "", 200


@app.route("/skip-back-short", methods=["POST"])
def skip_back_short():
    player.seek(SHORT_SKIP * -1)
    return "", 200


@app.route("/skip-forward-short", methods=["POST"])
def skip_forward_short():
    player.seek(SHORT_SKIP)
    return "", 200


@app.route("/skip-forward-long", methods=["POST"])
def skip_forward_long():
    player.seek(LONG_SKIP)
    return "", 200


@app.route("/skip-to", methods=["POST"])
def skip_to():
    hours = request.form.get("hours", 0, int)
    minutes = request.form.get("minutes", 0, int)
    seconds = request.form.get("seconds", 0, int)

    seconds += minutes * 60 + hours * 60 * 60
    player.skip_to(seconds)
    return "", 200


@app.route("/progress")
def progress():
    def _events():
        while True:
            time = player.get_time()
            if player.get_duration():
                progress = time / player.get_duration()
            else:
                progress = 0
            data = {
                "time": time,
                "progress": progress
            }
            event_string = f"data: {json.dumps(data)}\n\n".encode("utf-8")
            yield event_string
            sleep(1)

    return Response(_events(), mimetype="text/event-stream")
