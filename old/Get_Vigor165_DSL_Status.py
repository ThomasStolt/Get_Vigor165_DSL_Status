#
# The status of the DSL Connection in a Vigor 165 is available
# via SNMP from the OID 1.3.6.1.2.1.10.94.1.1.3.1.6.4 (adslAturCurrStatus)
# the values are the following:
# 53 48 4F 57 54 49 4D 45
# S  H  O  W  T  I  M  E
#
# 54 52 41 49 4E 49 4E 47 
# T  R  A  I  N  I  N  G
#
# 52 45 41 44 59
# R  E  A  D  Y

# IMPORTS
# =======
import os
import subprocess
from shutil import which
import time
from datetime import datetime

# Philips Hue Control
# ===================

from phue import Bridge
b = Bridge('192.168.2.94')
b.connect()
b.get_api()

def set_colour(colour):
    if colour == "red":
        value = (0.675, 0.322)
    elif colour == "yellow":
        value = (0.44, 0.515)
    elif colour == "green":
        value = (0.2151, 0.7106)
    b.set_light('ADSL1', 'on', True)
    b.set_light('ADSL1', 'xy', value)
    b.set_light('ADSL2', 'on', True)
    b.set_light('ADSL2', 'xy', value)
    b.set_light('ADSL3', 'on', True)
    b.set_light('ADSL3', 'xy', value)

def green_lights(value):
    set_colour("green")
    b.set_light('ADSL1', 'bri', 255 - value, transitiontime=0)
    b.set_light('ADSL2', 'bri', 255 - value, transitiontime=0)
    b.set_light('ADSL3', 'bri', 255 - value, transitiontime=0)

def lights_on_off(delay):
    b.set_light('ADSL1', 'bri', 255, transitiontime=0)
    b.set_light('ADSL2', 'bri', 255, transitiontime=0)
    b.set_light('ADSL3', 'bri', 255, transitiontime=0)
    time.sleep(delay)
    b.set_group(17, 'on', False, transitiontime=1)
    time.sleep(delay)

def lights_on(on_or_off):
    b.set_light('ADSL1', 'bri', 255, transitiontime=0)
    b.set_light('ADSL2', 'bri', 255, transitiontime=0)
    b.set_light('ADSL3', 'bri', 255, transitiontime=0)
    b.set_group(17, 'on', on_or_off, transitiontime=1)

# DEFINITIONS
# ===========
SNMP_GET_CMD = "snmpget"
SNMP_VERSION_OPT = "-v"
SNMP_VERSION = "1"
SNMP_RETRY_OPT = "-r"
SNMP_RETRY_COUNT = "0"
SNMP_COMMUNITY_OPTION = "-c"
SNMP_COMMUNITY = "public"
SNMP_TARGET_HOST= "192.168.2.2"
SNMP_OID = ".1.3.6.1.2.1.10.94.1.1.3.1.6.4"

# Strings to be matched for DSL Status
# ====================================
READY = "52 45 41 44 59"
TRAINING = "54 52 41 49 4E 49 4E 47"
SHOWTIME = "53 48 4F 57 54 49 4D 45"

# Check whether the snmpget command is existing
if not which(SNMP_GET_CMD):
    print("Error: snmpget command not found!")
    exit(1)

# Construct the snmpget command
snmpget_cmd = [SNMP_GET_CMD, SNMP_VERSION_OPT, SNMP_VERSION, SNMP_RETRY_OPT, SNMP_RETRY_COUNT, SNMP_COMMUNITY_OPTION, SNMP_COMMUNITY, SNMP_TARGET_HOST, SNMP_OID]

def get_adsl_status(delay):
    time.sleep(delay)
    CMD = subprocess.run(snmpget_cmd, capture_output=True)
    # If we encounter an error from snmpget command, catch and retry after 1 second
    while CMD.stderr.decode():
        print("Got error from snmpget command.")
        set_colour("red")
        b.set_light('ADSL1', 'bri', 255)
        b.set_light('ADSL2', 'bri', 255)
        b.set_light('ADSL3', 'bri', 255)
        b.set_group(17, 'on', True, transitiontime=1)
        CMD = subprocess.run(snmpget_cmd, capture_output=True)
    # We have a successful result from snmpget command, output is returned
    return(CMD.stdout.decode())

green_count = 2
set_colour("green")
lights_onoff = "on"
showtime_start = 0

while True:
    # Get the value of adslAturCurrStatus via SNMP
    STATUS = get_adsl_status(0)
    if SHOWTIME in STATUS:
        if showtime_start == 0:
            print("Entering showtime status: ", time.localtime())
            showtime_start = 1
        if green_count < 254:
            green_count += 4
            green_lights(green_count)
            if green_count == 254:
                b.set_group(17, 'on', False)
        time.sleep(1)

    elif TRAINING in STATUS:
        training_start = 0
        while TRAINING in STATUS:
            if training_start == 0:
                print ("Entering training status: ", time.localtime())
                start = 1
            STATUS = get_adsl_status(1)
            print("Training")
            set_colour("yellow")
            if lights_onoff == "on":
                lights_onoff = "off"
                lights_on(True)
            else:
                lights_onoff = "on"
                lights_on(False)
    elif READY in STATUS:
        ready_start = 0
        while READY in STATUS:
            if ready_start == 0:
                print ("Entering ready status: ", time.localtime())
            STATUS = get_adsl_status(0.3)
            print("ready")
            set_colour("red")
            if lights_onoff == "on":
                lights_onoff = "off"
                lights_on(True)
            else:
                lights_onoff = "on"
                lights_on(False)