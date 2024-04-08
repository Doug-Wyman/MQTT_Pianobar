# MQTT_Pianobar
 Inspiration from kylejohnson's Patiobar and a need to run Pianobar on a machine 
 seperate from the machine running Home Assistant spawned this creation.

 It all started with watchpb.py, a process that watches the Pianobar config folder.
 it is an event driven process that monitors any change in the folder.  Pianobar
 maintains and updates 4 files: config, currentSong, state and stationlist.
 On a folder change it passes updates information to the MQTT server.  

 watchpb also responds to a command file passed to the directory by the Home Assistant
 service: notify.nextsong. This is a service using the "file" platform which is a 
 Home Assistant log keeping service.  It saves the "Data: Message" information to
 the confg folder.  To simplify the use within the Home assistant docker instance this
 folder is mounted into the Home assistant folder.

 I wasn't going to publish this but was prompted by discussion on Kyle Johnson's 
 Patiobar "Issues" https://github.com/kylejohnson/Patiobar/issues/43 to explore the 
 CLI output from Pianobar.  That led to the creation of pb_shell.py which initiates
 an instance of Pianobar and monitors the CLI output for the keywords "#", "(i)",
 "|>", "\t 0)", "\t 1)", "\t 2)" and forwards the info to the MQTT server.

 An annoyance/bug to the shell is that the shell can end without stopping Pianobar.
 If it is reopened there will be two (or more) instances of Pianobar running.

 Let me know if I have missed anything.  CRS at 81 I forget a lot.

Files:
  mqtt.yaml initializes the Home Assistant mqtt sensors 
  service is the configuration.yaml entry for the nextsong service



 


