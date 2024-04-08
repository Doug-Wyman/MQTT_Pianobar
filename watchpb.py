'''
**************************************************************
A Mosquitto process that watches the Pianobar config folder.
The Pianobar config folder is mounted as pianobar under the homeassistant folder.
PianoBar maintains 4 files in the folder: state , config, currentSong and stationList
This folder is also where HomeAssistant places the output from service.nextsong

****config.yaml entry*****
notify:
  - name: NextSong
    platform: file
    filename: 'pianobar/nextsong'
***************************

The Homeassistant notify platform "file" appends a "log file"
If the file does not exist, it is created with a timestamp as the first entry.
The notify creates a new-line in the "log" with the message sent by the notify service
This process reads that file and if needed, sends keystrokes to the Pianobar ctl
folder with an os.system echo and/or updates internal variables and reports.
*****************************************************************
'''

import os
from os.path import exists
import time
import urllib.request
import json
import paho.mqtt.publish as publish
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class OnMyWatch:
    '''
    ******************************************
    This is the class that sets up the event handler
    any change to the Pianobar config folder triggers
    the code that looks at the changes made and processes them
    ******************************************
    '''

    # Set the directory on watch
    watchDirectory = "/home/pi/.config/pianobar"
    global NEWCMD, COUNTDOWN, LASTINFO
    def __init__(self):
        self.observer = Observer()
    def run(self):
        '''
        This is where the system kicks off
        '''
        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDirectory, recursive = True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except OSError:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()

class Handler(FileSystemEventHandler):
    '''
    This handles the folder change event

    *******************************
    the following 3 variables: pb_config, mqtt_host and image_dir
    must be set to the addresses of the folders and mqtt host
    in your installation
    *******************************
    '''
    @staticmethod
    def on_any_event(event):
        global NEWCMD, COUNTDOWN, LASTINFO

        pb_config = "/home/pi/.config/pianobar/"
        mqtt_host = "192.168.0.109"
        image_dir = "/var/www/html/images/"
        print("Source of change=" + event.src_path)

        if event.src_path == pb_config + "stationList":
            if exists(pb_config + "stationList"):
                try:
                    station_list = open(pb_config + "stationList")
                    stalist = station_list.read().split('\n')
                    station_list.close()
                    try:
                        publish.single('/sensor/pianobar/stations',
                        json.dumps(stalist), hostname=mqtt_host)
                    except OSError:
                        print("client error")
                except OSError:
                    print("open error")

        if event.src_path == pb_config + "currentSong":
            print("Changed the song")
            publish.single("/sensor/pianobar/list1","No List",hostname=mqtt_host)
            publish.single("/sensor/pianobar/list2","No List",hostname=mqtt_host)
            publish.single("/sensor/pianobar/list3","No List",hostname=mqtt_host)
            os.system("echo -n 'u' > ~/Patiobar/ctl")
            try:
                publish.single('/sensor/pianobar/countdown', COUNTDOWN, hostname=mqtt_host)
            except OSError:
                print("client error")

            if int(COUNTDOWN) > -1:
                COUNTDOWN = str(int(COUNTDOWN) -1)
                try:
                    #publish.single('/pianobar/nextsong', NEWCMD, hostname=mqtt_host)
                    publish.single('/sensor/pianobar/nextsong', NEWCMD, hostname=mqtt_host)
                except OSError:
                    print("client error")
                if int(COUNTDOWN) <= 0:
                    COUNTDOWN = -1
                    os.system("echo -n 'p' > ~/Patiobar/ctl")
                    if os.path.exists(pb_config + "nextsong"):
                        os.remove(pb_config + "nextsong")
                    NEWCMD = ""
            newimg = open(pb_config + "currentSong")
            imgurl = newimg.read()
            newimg.close()
            parseimgurl = imgurl.split(",,,")
            savfile = ""
            newfile = ""
            savfile = ""
            if len(parseimgurl) > 2:
                try:
                    newfile = parseimgurl[3].split("/")
                    savfile = newfile[len(newfile) - 1]
                    print("SAVE" + savfile)
                    urllib.request.urlretrieve(parseimgurl[3], image_dir + "currentsong.jpg")
                    print("Saved - " + parseimgurl[3])
                    print("NewFile:" + savfile)
                    os.rename(image_dir + "currentsong.jpg", image_dir + savfile)
                except OSError:
                    pass
                except ValueError:
                    pass
                try:
                    infolist = imgurl.split(',,,')
                    print(infolist)
                    print(savfile)
                    infolist[3] = "http://192.168.0.108/images/" + savfile
                    if infolist[4] == "0":
                        infolist[4] = "OFF"
                    else:
                        infolist[4] = "ON"
                    LASTINFO = infolist
                    publish.single('/sensor/pianobar/newsong',
                    json.dumps(infolist), hostname=mqtt_host)
                    print("published")
                except OSError:
                    pass
                try:
                    publish.single('/sensor/pianobar/newsong',
                    json.dumps(infolist), hostname=mqtt_host)
                except OSError:
                    print("client error")

        if event.src_path == pb_config + "nextsong":
            print(exists(pb_config + "nextsong"))
            if not exists(pb_config + "nextsong"):
                return
            print("Received Command")
            print("old Command " + NEWCMD)
            try:
                rawcmd = open(pb_config + "nextsong")
                tmpcmd = rawcmd.read()
                print("new Command " + tmpcmd)
                NEWCMD = tmpcmd.split('\n')
                print(NEWCMD)
                #NEWCMD = NEWCMD[0]
                if NEWCMD[len(NEWCMD) -1] == "":
                    NEWCMD = NEWCMD[len(NEWCMD) - 2]
                else:
                    NEWCMD = NEWCMD[len(NEWCMD) -1]
                print("new Command " + NEWCMD)
                rawcmd.close()
            except OSError as my_os_error:
                print("Big Error")
                print(my_os_error)
            try:
                publish.single('/sensor/pianobar/nextsong', NEWCMD, hostname=mqtt_host)
            except OSError:
                print("client error")
            if NEWCMD != "":
                # if NEWCMD == "onnextpause":
                    # print("pause/play")
                    # try:
                        # COUNTDOWN=0
                        # NEWCMD = ""
                        # os.remove(pb_config + "nextsong")
                    # except OSError:
                        # print("error echo")

                if NEWCMD == "next":
                    print("changing to next song")
                    try:
                        os.system("echo -n 'n' > ~/Patiobar/ctl")
                        NEWCMD = ""
                    except OSError:
                        print("error echo")
                    try:
                        if os.path.exists(pb_config + "nextsong"):
                            os.remove(pb_config + "nextsong")
                        NEWCMD = ""
                    except OSError:
                        print("error echo")
                    if os.path.exists(pb_config + "nextsong"):
                        os.remove(pb_config + "nextsong")

                if NEWCMD == "tired":
                    print("changing to next song")
                    try:
                        os.system("echo -n 't' > ~/Patiobar/ctl")
                        NEWCMD = ""
                    except OSError:
                        print("error echo")
                    try:
                        if os.path.exists(pb_config + "nextsong"):
                            os.remove(pb_config + "nextsong")
                        NEWCMD = ""
                    except OSError:
                        print("error echo")
                    if os.path.exists(pb_config + "nextsong"):
                        os.remove(pb_config + "nextsong")

                if NEWCMD == "pause":
                    print("pause/play")
                    try:
                        os.system("echo -n 'p' > ~/Patiobar/ctl")
                        NEWCMD = ""
                    except OSError:
                        print("error echo")
                    if os.path.exists(pb_config + "nextsong"):
                        os.remove(pb_config + "nextsong")

                if NEWCMD[0:8] == "playlist":
                    publish.single("/sensor/pianobar/list1",
                    "No List",hostname=mqtt_host)
                    publish.single("/sensor/pianobar/list2",
                    "No List",hostname=mqtt_host)
                    publish.single("/sensor/pianobar/list3",
                    "No List",hostname=mqtt_host)
                    os.system("echo -n 'u' > ~/Patiobar/ctl")
                    try:
                        publish.single('/sensor/pianobar/nextsong',
                        NEWCMD, hostname=mqtt_host)
                    except OSError:
                        print("client error")

                if NEWCMD == "like":
                    os.system("echo -n '+' > ~/Patiobar/ctl")
                    NEWCMD = ""
                    if os.path.exists(pb_config + "nextsong"):
                        os.remove(pb_config + "nextsong")
                    try:
                        infolist = LASTINFO
                        infolist[4] = "ON"
                        publish.single('/sensor/pianobar/newsong',
                        json.dumps(infolist), hostname=mqtt_host)
                    except OSError:
                        print("client error")

                if NEWCMD == "refresh":
                    NEWCMD = ""
                    if os.path.exists(pb_config + "nextsong"):
                        os.remove(pb_config + "nextsong")
                    print("Refresh")
                    try:
                        infolist = LASTINFO
                        publish.single('/sensor/pianobar/newsong',
                        json.dumps(infolist), hostname=mqtt_host)
                        publish.single('/sensor/pianobar/countdown',
                        str(COUNTDOWN), hostname=mqtt_host)
                    except OSError:
                        print("client error")

                if NEWCMD[0:7] == "station":
                    newsta = NEWCMD[7:]
                    os.system("echo -n 's" + newsta + "\n' > ~/Patiobar/ctl")
                    NEWCMD = ""
                    if os.path.exists(pb_config + "nextsong"):
                        os.remove(pb_config + "nextsong")

                if NEWCMD[0:9] == "countdown":
                    COUNTDOWN = NEWCMD[9:]
                    print("Set countdown to" + str(COUNTDOWN) )
                    NEWCMD = ""
                    if os.path.exists(pb_config + "nextsong"):
                        os.remove(pb_config + "nextsong")
                    try:
                        publish.single('/sensor/pianobar/countdown',
                        str(COUNTDOWN), hostname=mqtt_host)
                    except OSError:
                        print("client error")

                if os.path.exists(pb_config + "nextsong"):
                    os.remove(pb_config + "nextsong")


if __name__ == '__main__':
    LASTINFO = ""
    NEWCMD = ""
    COUNTDOWN = -1
    watch = OnMyWatch()
    watch.run()
