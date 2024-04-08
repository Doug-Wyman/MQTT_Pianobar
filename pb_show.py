'''
**********************************************
This process loads Pianobar into a subprocess.
It monitors the stdout from Pianobar and publishes
the countdown timer, any information lines, the
playlist entries and new song information.
************************************************
'''

import subprocess
import paho.mqtt.publish as publish

with subprocess.Popen('pianobar', shell=True, stdout=subprocess.PIPE, text=True) as process:
    for line in process.stdout:
        line = line[4:]
        if line[0:1] == "#":
            print("TIME: " + line[5:len(line) -1], end = "\r")
            publish.single("/sensor/pianobar/time",line[5:len(line) -1],hostname="192.168.0.109")
        elif line[0:3] == "(i)":
            print("Info" + line[4:])
            publish.single("/sensor/pianobar/info",line[4:],hostname="192.168.0.109")
        elif line[0:2] == "|>":
            print("Song Info: " + line[4:])
        elif line[0:4] == "\t 0)":
            print("Upcoming: " + line[2:])
            publish.single("/sensor/pianobar/list1",line[2:],hostname="192.168.0.109")
        elif line[0:4] == "\t 1)":
            print("Upcoming1: " + line[2:])
            publish.single("/sensor/pianobar/list2",line[2:],hostname="192.168.0.109")
        elif line[0:4] == "\t 2)":
            print("Upcoming2: " + line[2:])
            publish.single("/sensor/pianobar/list3",line[2:],hostname="192.168.0.109")
        else:
            print(f"Received: {line[0:]}")
