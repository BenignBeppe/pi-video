import logging
import json
from queue import Queue
import math
from datetime import datetime
from datetime import timezone

from flask import jsonify
from flask import render_template
from flask import request
from flask import abort
from flask import Response
from flask import redirect
from flask import url_for
from vlc import Instance
from vlc import EventType
from youtube_dl import YoutubeDL

from app import app
from app import db
from app.models import Video


SHORT_SKIP = 10
LONG_SKIP = 60


class Player:
    def __init__(self):
        self._instance = Instance()
        self._player = self._instance.media_player_new()
        self.vlc_events = self._player.event_manager()
        self.vlc_events.event_attach(
            EventType.MediaPlayerTimeChanged,
            self._update_time
        )
        self.vlc_events.event_attach(
            EventType.MediaPlayerLengthChanged,
            self._update_duration
        )
        self.page_url = None
        self.event_queues = set()
        self._last_event_time = 0

    def _update_time(self, event):
        time = math.floor(self.get_time())
        if time != 0 and time % 60 == 0:
            # Save time every full minute.
            self._save_time(time)

        if time == self._last_event_time:
            # Don't send an event unless the time has changed
            # noticably.
            return

        if _player.get_duration():
            progress = time / _player.get_duration()
        else:
            progress = 0
        data = {
            "time": time,
            "progress": progress
        }
        self._send_event("time", data)
        self._last_event_time = time

    def _save_time(self, time):
        video = Video.query.filter_by(page_url=self.page_url).first()
        if video is None:
            return

        if video.time == time:
            return

        video.time = time
        video.last_played = datetime.now(timezone.utc)
        db.session.add(video)
        db.session.commit()

    def _send_event(self, type, data=""):
        for queue in self.event_queues:
            queue.put({"type": type, "data": data})

    def _update_duration(self, event):
        self._send_event("duration", self.get_duration())

    def load(self, page_url):
        self._send_event("loading")
        logging.info(f"Loading video from {page_url}.")
        self.page_url = page_url
        video = Video.query.filter_by(page_url=page_url).first()
        if video is None:
            video = Video(page_url)
        if video.video_url is None:
            logging.debug("Fetching video URL from page.")
            ydl_opts = {
                "format": "[tbr<2500]",
                "forceurl": True
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(page_url, download=False)
                video.video_url = info["url"]
                video.title = info["title"]
                logging.debug(f"Video URL retrieved: {video.video_url}.")
        logging.info(f"Video URL: {video.video_url}.")
        media = self._instance.media_new(video.video_url)
        media.parse()
        self._player.set_media(media)
        logging.info("Starting playback.")
        self._player.play()
        if video.time:
            self.skip_to(video.time)
        video.last_played = datetime.now(timezone.utc)
        db.session.add(video)
        db.session.commit()

    def seek(self, amount):
        time = self.get_time()
        if time is None:
            return

        new_time = time + amount
        self.skip_to(new_time)
        return new_time

    def skip_to(self, time):
        self._player.set_time(int(time * 1000))
        self._save_time(time)

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

    def is_playing(self):
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


_player = Player()


@app.route("/player")
@app.route("/")
def player():
    time = _player.get_time()
    duration = _player.get_duration()
    if duration:
        progress = time / duration * 100
    else:
        progress = 0
    page_url = _player.page_url
    if page_url is None:
        page_url = ""
    time_string = _player.get_time_string()
    duration_string = _player.get_duration_string()
    parameters = {
        "time": time_string,
        "duration": duration_string,
        "progress": progress,
        "video_url": page_url
    }
    return render_template("player.html", **parameters)


@app.route("/load", methods=["GET", "POST"])
def load():
    if request.method == 'POST':
        page_url = request.form.get("url")
        if not page_url:
            abort(400, description="Missing required parameter 'url'.")

        _player.load(page_url)
        return jsonify(duration=_player.get_duration())
    else:
        page_url = request.args.get("url")
        if page_url:
            _player.load(page_url)
        return redirect(url_for("player"))


@app.route("/play-pause", methods=["POST"])
def play_pause():
    _player.play_pause()
    return "", 200


@app.route("/skip-back-long", methods=["POST"])
def skip_back_long():
    _player.seek(LONG_SKIP * -1)
    return "", 200


@app.route("/skip-back-short", methods=["POST"])
def skip_back_short():
    _player.seek(SHORT_SKIP * -1)
    return "", 200


@app.route("/skip-forward-short", methods=["POST"])
def skip_forward_short():
    _player.seek(SHORT_SKIP)
    return "", 200


@app.route("/skip-forward-long", methods=["POST"])
def skip_forward_long():
    _player.seek(LONG_SKIP)
    return "", 200


@app.route("/skip-to", methods=["POST"])
def skip_to():
    hours = request.form.get("hours", 0, int)
    minutes = request.form.get("minutes", 0, int)
    seconds = request.form.get("seconds", 0, int)

    seconds += minutes * 60 + hours * 60 * 60
    _player.skip_to(seconds)
    return "", 200


@app.route("/events")
def events():
    logging.debug("Event connection opened.")
    queue = Queue()
    _player.event_queues.add(queue)

    def _events():
        try:
            while True:
                event = queue.get()
                logging.debug(f"Sending event: {event}.")
                data = json.dumps(event["data"])
                event_string = f"event: {event['type']}\ndata: {data}\n\n"
                yield event_string.encode("utf-8")
        finally:
            _player.event_queues.discard(queue)
            logging.debug("Event connection lost.")

    return Response(_events(), mimetype="text/event-stream")
