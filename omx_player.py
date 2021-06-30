import logging
import dbus
import getpass
import os

from omxplayer.player import OMXPlayer

class OmxPlayer:
    def __init__(self):
        self._omx = None

    # def _setup_dbus(self):
    #     omxplayer_dbus_address = "/tmp/omxplayerdbus.root"
    #     os.environ["DBUS_SESSION_BUS_ADDRESS"] = \
    #         open(omxplayer_dbus_address).read().rstrip()
    #     omxplayer_dbus_pid = "/tmp/omxplayerdbus.root.pid"
    #     os.environ["DBUS_SESSION_BUS_PID"] = \
    #         open(omxplayer_dbus_pid).read().rstrip()
    #     bus = dbus.SessionBus()
    #     # FIXME
    #     self._omx = bus.get_object(
    #         "org.mpris.MediaPlayer2.omxplayer",
    #         "/org/mpris/MediaPlayer2"
    #     )
    #     logging.debug("DBus setup properly.")

    # def _call_dbus(self, method_name, *args):
    #     self._setup_dbus()
    #     if self._omx is None:
    #         raise Exception("No media player DBus object.")
    #     try:
    #         logging.debug("Calling DBus method: {}{}".format(method_name, args))
    #         return self._omx.get_dbus_method(method_name)(*args)
    #     except:
    #         raise Exception("Failed to call BDus method.")

    def get_time(self):
        microseconds = self._call_dbus("Position")
        time = microseconds / 10 ** 6
        return time

    def get_duration(self):
        if self._omx == None:
            return None
        return self._omx.duration()

    def get_playing(self):
        status = self._call_dbus("PlaybackStatus")
        return status == "Playing"

    def play_pause(self):
        self._call_dbus("PlayPause")

    def stop(self):
        self._call_dbus("Quit")

    def seek(self, duration):
        microseconds = int(duration * 10 ** 6)
        self._call_dbus("Seek", dbus.Int64(microseconds))
        logging.debug("Seeked: {}".format(duration))
        return self.get_time()
        return time

    def skip(self, time):
        microseconds = hours * 60 * 60 * 1000000 + \
            minutes * 60 * 1000000 + \
            seconds * 1000000
        result = self._call_dbus(
            "SetPosition",
            dbus.ObjectPath("/not/used"),
            dbus.Int64(microseconds)
        )
        return result

    def load(self, url):
        logging.info("Starting omxplayer for URL: {}".format(url))
        self._omx = OMXPlayer(url, args=["-o", "hdmi", "--no-boost-on-downmix"])
        # logging.debug("Calling omxplayer: {}".format(" ".join(omxplayer_command)))
        # subprocess.Popen(omxplayer_command)
