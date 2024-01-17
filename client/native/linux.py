import dbus
import subprocess

def setPlayerVolume(playerName, value):
    sinks = str(subprocess.run(['pactl', 'list', 'sink-inputs'], stdout=subprocess.PIPE, encoding="utf-8").stdout)
    for i in sinks.split("Sink Input #"):
        if f'application.name = "{playerName}"' in i:
            sinkID = i.split("\n")[0]
            print(f"[INFO] Setting volume for sink {playerName} (sinkid {sinkID}) to {value}")
            subprocess.run(["pactl", "set-sink-input-volume", sinkID, f"{value}%"], stdout=subprocess.DEVNULL)

class Mixer:
    def __init__(self, config):
        self.session_bus = dbus.SessionBus()
        self.config = config

    def getMediaData(self):
        for service in self.session_bus.list_names():
            if service.startswith("org.mpris.MediaPlayer2."):
                try:
                    player = dbus.SessionBus().get_object(service, '/org/mpris/MediaPlayer2')
                    metadata = player.Get('org.mpris.MediaPlayer2.Player', 'Metadata', dbus_interface="org.freedesktop.DBus.Properties")
                    return {
                        "title": metadata['xesam:title'],
                        "artist": metadata['xesam:artist'][0]
                    }
                except:
                    continue
        return {
            "title": "Please play", "artist": "something."
        }

    def setVolume(self, vtype, value):
        if vtype == 'system':
            print(f"[INFO] Setting system volume to {value}% using amixer...")
            subprocess.run(["amixer", "set", "'Master'", f"{value}%"], stdout=subprocess.DEVNULL)
        else:
            print(f"[INFO] Setting volume for category '{vtype}' to {value}% using pactl...")
            sinks = self.config[vtype]['sinks']
            for i in sinks:
                setPlayerVolume(i, value)
