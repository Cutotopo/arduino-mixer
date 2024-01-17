from comtypes import CLSCTX_ALL
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as media
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
import asyncio

async def getMediaData():
    sessions = await media.request_async()
    currentSession = sessions.get_current_session()
    if currentSession:
        info = await currentSession.try_get_media_properties_async()
        info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}
        return {
            "title": info_dict['title'],
            "artist": info_dict['artist']
        }
    else:
        return {
            "title": "Please play",
            "artist": "something."
        }

class Mixer:
    def __init__(self, config):
        self.config = config

    def getMediaData(self):
        return asyncio.run(getMediaData())
    
    def setVolume(self, vtype, value):
        if vtype == 'system':
            print(f"[INFO] Setting system volume to {value}%...")
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMasterVolumeLevelScalar(value / 100, None)
        else:
            print(f"[INFO] Setting volume for category '{vtype}' to {value}%...")
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                interface = session.SimpleAudioVolume
                if session.Process and session.Process.name() in self.config[vtype]['sinks']:
                    interface.SetMasterVolume(value / 100, None)