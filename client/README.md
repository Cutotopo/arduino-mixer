# ArduinoMixer - Client Software
This directory contains the client software for the ArduinoMixer project. Dedicated modules are used for OS-specific interactions.

### Linux module
Media metadata is obtained using MPRIS2, and volumes are set using amixer and pactl.

### Windows module
Media metadata is obtained using GlobalSystemMediaTransportControlsSessionManager (WinRT), and volumes are set using pycaw.
