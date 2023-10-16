# import MQTT library
import paho.mqtt.client as mqtt
import time
import json
import requests
import os
from phue import Bridge

HUE_BRIDGE_IP = "PhilipsHueBridge"
API_KEY_FILE_NAME = "Philips_Hue_API_Key.txt"
MQTT_BROKER_HOST = "192.168.2.53"
MQTT_TOPIC = "ADSL_status"
GROUP_NR = "17"
HEADERS = { 'Accept': 'application/json' }

# This will switch the lights on and set the brightness to bri. The colour of
# the lights will be whatever the last colour of that light was. This is needed
# in case the lights are off and we want to change the colour. If the lights
# are off and we try to change the colour, it will fail.
def lights_on(bri):
    requests.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data=f'{{"on": true, "bri": {bri}, "transitiontime": 0}}')

# This will switch the lights off
def lights_off():
    requests.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data=f'{{"on": false, "transitiontime": 0}}')

# This will only set the colour (red, yellow or green) fast, brightness will be unchanged
# That also means that if it is off, it will stay off
def set_colour(colour):
    if   colour == "red":    colour = '{ "xy": [0.6750, 0.3220], "transitiontime":0 } '
    elif colour == "yellow": colour = '{ "xy": [0.4684, 0.4759], "transitiontime":0 } '
    elif colour == "green":  colour = '{ "xy": [0.2151, 0.7106], "transitiontime":0 } '
    requests.put("http://" + HUE_BRIDGE_IP + "/api/"  + API_KEY + "/groups/" + GROUP_NR + "/action/", headers=HEADERS, data=colour)

# This will set the brightness to the value provided
# The colour will stay unchanged
def new_bri(value):
    requests.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data=f'{{"bri": {value}, "transitiontime": 0}}')

# If lights are off turn them on, if they are on turn them off
def toggle_lights():
    # Find out whether any of the ADSL lights are on
    dict = requests.get(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}")
    if json.loads(dict.text)['state']['any_on']:
        requests.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data='{"on":false, "bri": 0, "transitiontime": 0}')
    else:
        requests.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data='{"on":true, "bri": 254, "transitiontime": 0}')

# Check if the API key file exists
if os.path.exists(API_KEY_FILE_NAME):
    # Fetch the API key from the key file
    with open(API_KEY_FILE_NAME, 'r') as keyfile:
        API_KEY = keyfile.read()
else:
    print(f"Error: File '{API_KEY_FILE_NAME}' does not exist!")
    exit(1)

# Set the duration for the loop (60 seconds)
duration_seconds = 20
iterations = int(duration_seconds / 1)  # Run for 1 second per iteration

for _ in range(iterations):
    # Toggle the lights on and off every 0.5 seconds
    lights_on(20)
    set_colour("red")
    time.sleep(1)
    lights_off()
    time.sleep(1)
