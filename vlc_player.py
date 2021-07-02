import logging

import vlc

class VlcPlayer:
    def __init__(self):
        self._instance = vlc.Instance()
        self._player = self._instance.media_player_new()

    def load(self, url):
        logging.debug("Loading from URL: {}".format(url))
        # self._player = vlc.MediaPlayer(url)
        # self._player.set_mrl("rtsp://{}".format(url))
        media = self._instance.media_new(url)
        # media.get_mrl()
        self._player.set_media(media)
        self._player.play()

    def seek(self, amount):
        time = self.get_time()
        if time == None:
            return

        new_time = time + amount
        self.skip(new_time)

    def skip(self, time):
        self._player.set_time(int(time * 1000))

    def play_pause(self):
        self._player.pause()

    def get_duration(self):
        duration = self._player.get_length()
        if duration == -1:
            return

        return duration / 1000

    def get_time(self):
        time = self._player.get_time()
        if time == -1:
            return

        return time / 1000

    def get_playing(self):
        return self._player.is_playing() == 1
