# ======= #
# IMPORTS #
# ======= #
import json
import requests
import subprocess
import time
import sys
import os
from time import gmtime, strftime
from shutil import which

#=============#
# DEFINITIONS #
#=============#
HUE_BRIDGE_IP = "PhilipsHueBridge"
API_KEY_FILE_NAME = "Philips_Hue_API_Key.txt"
GROUP_NR = "17"
HEADERS = { 'Accept': 'application/json' }
SNMP_GET_CMD = "snmpget"
SNMP_VERSION_OPT = "-v"
SNMP_VERSION = "1"
SNMP_RETRY_OPT = "-r"
SNMP_RETRY_COUNT = "0"
SNMP_COMMUNITY_OPTION = "-c"
SNMP_COMMUNITY = "public"
SNMP_TARGET_HOST= "192.168.2.2"
SNMP_OID = ".1.3.6.1.2.1.10.94.1.1.3.1.6.4"
READY = "52 45 41 44 59"
TRAINING = "54 52 41 49 4E 49 4E 47"
SHOWTIME = "53 48 4F 57 54 49 4D 45"

#===========#
# FUNCTIONS #
#===========#

# This will switch the lights on and set the brightness to bri
# The colour of the lights will be whatever the last colour of that light was
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

def get_adsl_status(delay):
    time.sleep(delay)
    CMD = subprocess.run(snmpget_cmd, capture_output=True)
    # If we encounter an error from snmpget command, catch and retry after 2 seconds
    # Sometimes, if the router is not ready rebooting, it will take some time for the response
    error_start = 0
    while CMD.stderr.decode():
        if error_start == 0:
            print("Entering error status: ", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
            sys.stdout.flush()
            error_start = 1
            set_colour("red")
            lights_on(254)
        CMD = subprocess.run(snmpget_cmd, capture_output=True)
        time.sleep(2)
    # We have a successful result from snmpget command, output is returned
    return(CMD.stdout.decode())

#==============================================================================#

#=======#
# START #
#=======#

# Check if the API key file exists
if os.path.exists(API_KEY_FILE_NAME):
    # Fetch the API key from the key file
    with open(API_KEY_FILE_NAME, 'r') as keyfile:
        API_KEY = keyfile.read()
else:
    print(f"Error: File '{API_KEY_FILE_NAME}' does not exist!")
    exit(1)


# Check whether the snmpget command is existing
if not which(SNMP_GET_CMD):
    print("Error: snmpget command not found!")
    exit(1)

# Construct the snmpget command
snmpget_cmd = [SNMP_GET_CMD, SNMP_VERSION_OPT, SNMP_VERSION, SNMP_RETRY_OPT, SNMP_RETRY_COUNT, SNMP_COMMUNITY_OPTION, SNMP_COMMUNITY, SNMP_TARGET_HOST, SNMP_OID]

# Main loop
while True:
    # Get the value of adslAturCurrStatus via SNMP
    STATUS = get_adsl_status(1)

    # If we find SHOWTIME in STATUS slowly dim the green light down and continue
    # to query status, every 5 seconds is fast enough
    showtime_start = 0
    green_count = 254
    lights_on(1)
    while SHOWTIME in STATUS:
        # Print line with date time stamp only the first time in this loop
        if showtime_start == 0:
            print("Entering showtime status: ", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
            sys.stdout.flush()
            set_colour("green")
            showtime_start = 1
        if green_count > 0:
            new_bri(green_count)
            # decrement green_count by 1
            green_count -= 1
            if green_count == 1:
                lights_off()
        time.sleep(5)
        STATUS = get_adsl_status(0)

    # If we find TRAINING in STATUS
    training_start = 0
    while TRAINING in STATUS:
        # Print line with date time stamp only the first time in this loop
        if training_start == 0:
            print ("Entering training status: ", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
            sys.stdout.flush()
            set_colour("yellow")
            training_start = 1
            new_bri(254)
        toggle_lights()
        STATUS = get_adsl_status(2)

    # If we finde READY in STATUS
    ready_start = 0
    while READY in STATUS:
        # Print line with date time stamp only first time in this loop
        if ready_start == 0:
            print("Entering ready status: ", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
            sys.stdout.flush()
            ready_start = 1
            set_colour("red")            
            new_bri(254)
            time.sleep(1)
        toggle_lights()
        STATUS = get_adsl_status(0.5)