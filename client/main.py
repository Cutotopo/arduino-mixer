from sys import platform

# Import platform-specific modules
if platform == 'linux':
    from native.linux import Mixer
elif platform == 'win32':
    from native.windows import Mixer
else:
    print(f"[CRIT] Unsupported platform '{platform}'. Check the top of main.py and add your platform there.")
    exit(1)

import json
import serial
from time import sleep

# Get config
f = open("config.json", "r")
config = json.loads(f.read())
f.close()

mixer = Mixer(config)
ser = None
prevData = {}
quit = False

# Encode and prepare metadata message for sending to Arduino
def getMetadataMessage(data):
    oTitle = data['title']
    oArtist = data['artist']
    out = f"{data['title']}\v{data['artist']}\n"
    # Check if the message is too long before sending
    if (len(out) > 64):
        # If the message is too long, the title or artist will be cut to 29 characters and an ellipsis ("...") will be appended
        if (len(oTitle) > 32):
            oTitle = data['title'][:29] + (data['title'][29:] and "...")
        if (len(oArtist) > 32):
            oArtist = data['artist'][:25] + (data['artist'][25:] and "...")
        return f"{oTitle}\v{oArtist}\n".encode('ascii', 'ignore')
    else:
        return out.encode('ascii', 'ignore')

# Parse received serial command
def parseSerialCommand(cmd):
    try:
        j = json.loads(cmd)
        print("[INFO] Received valid command from Arduino.")
        if j['t'] == 'v':
            mixer.setVolume(config['sources'][j['ch']], j['val'])
        if j['t'] == 'r':
            print("[INFO] Arduino is waiting for configuration.")
            print("[INFO] Sending out Arduino configuration.")
            for i in config['sources']:
                ser.write(f"{config[i]['label']}\n".encode('ascii', 'ignore'))
        if j['t'] == 'm':
            print("[INFO] Arduino requested current metadata.")
            print(f"[INFO] Sent out metadata: '{prevData['title']}' by '{prevData['artist']}'")
            ser.write(getMetadataMessage(prevData))
    except:
        # Handle invalid commands
        print(f"[WARN] Received invalid command from Arduino. ({cmd})")

# Attempt to open a serial connection to the Arduino
def openSerial():
    global ser;
    try:
        ser = serial.Serial(config['arduinoPath'])
        print("[INFO] Connection with Arduino established. Starting up...")
    except serial.SerialException:
        print(f"[WARN] Could not connect to Arduino. Check connection on port {config['arduinoPath']}. Will try again in 5 seconds.")
        sleep(5)

# Main program loop
def mainLoop():
    global ser, prevData
    # Get current media data
    data = mixer.getMediaData()
    # Check if the current media data is different from the previous version
    if data != prevData:
        # Send encoded data to Arduino
        ser.write(getMetadataMessage(data))
        print(f"[INFO] Sent out metadata: '{data['title']}' by '{data['artist']}'")
        prevData = data
    # If there is a command from the Arduino, parse it
    if (ser.in_waiting > 0):
        serin = ser.read(ser.in_waiting).decode('ascii')
        parseSerialCommand(serin)
    sleep(0.05)

try:
    while not quit:
        if ser is None:
            openSerial();
        else:
            try:
                mainLoop()
            except OSError:
                print("[WARN] Lost connection with Arduino!")
                ser = None
except KeyboardInterrupt:
    print("Exiting...")
    if ser is not None:
        ser.close()
