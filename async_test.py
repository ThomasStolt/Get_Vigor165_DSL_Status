# ======= #
# IMPORTS #
# ======= #
import json
import requests
import subprocess
import time
import sys
import os
import aiohttp
import asyncio
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

async def lights_on(bri):
    print("DEBUG: Entering lights_on function...")
    async with aiohttp.ClientSession() as session:
        await session.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data=f'{{"on": true, "bri": {bri}, "transitiontime": 0}}')
    print("DEBUG: Completed lights_on function.")

async def lights_off():
    print("DEBUG: Entering lights_off function...")
    async with aiohttp.ClientSession() as session:
        await session.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data=f'{{"on": false, "transitiontime": 0}}')
    print("DEBUG: Completed lights_off function.")

async def set_colour(colour):
    print(f"DEBUG: Entering set_colour function with colour: {colour}...")
    async with aiohttp.ClientSession() as session:
        if   colour == "red":    colour = '{ "xy": [0.6750, 0.3220], "transitiontime":0 } '
        elif colour == "yellow": colour = '{ "xy": [0.4684, 0.4759], "transitiontime":0 } '
        elif colour == "green":  colour = '{ "xy": [0.2151, 0.7106], "transitiontime":0 } '
        await session.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data=colour)
    print("DEBUG: Completed set_colour function.")

async def new_bri(value):
    print(f"DEBUG: Entering new_bri function with value: {value}...")
    async with aiohttp.ClientSession() as session:
        await session.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data=f'{{"bri": {value}, "transitiontime": 0}}')
    print("DEBUG: Completed new_bri function.")

async def toggle_lights():
    print("DEBUG: Entering toggle_lights function...")
    async with aiohttp.ClientSession() as session:
        response = await session.get(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}")
        data = await response.json()
        if data['state']['any_on']:
            await session.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data='{"on":false, "bri": 0, "transitiontime": 0}')
        else:
            await session.put(f"http://{HUE_BRIDGE_IP}/api/{API_KEY}/groups/{GROUP_NR}/action/", headers=HEADERS, data='{"on":true, "bri": 254, "transitiontime": 0}')
    print("DEBUG: Completed toggle_lights function.")

previous_adsl_status = None

async def slowly_dim_lights():
    print("DEBUG: Entering slowly_dim_lights function...")
    for bri_value in range(254, 0, -10):  # Start from full brightness and decrease by 10 units in each step. Adjust as needed.
        await new_bri(bri_value)
        await asyncio.sleep(1)  # Wait for 1 second between each step. Adjust as needed.
    print("DEBUG: Completed slowly_dim_lights function.")

async def get_adsl_status(delay):
    print(f"DEBUG: Entering get_adsl_status function with delay: {delay}...")
    await asyncio.sleep(delay)
    
    process = subprocess.Popen(snmpget_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = process.communicate()
    
    # Handle errors just like the original function
    error_start = False
    while stderr_data:
        if not error_start:
            print(f"Entering error status at: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}")
            error_start = True
            await set_colour("red")
            await lights_on(254)
        
        process = subprocess.Popen(snmpget_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = process.communicate()
        await asyncio.sleep(2)
    
    status = stdout_data.decode().strip()
    print(f"DEBUG: ADSL status obtained: {status}")
    return status

async def check_snmp_status():
    global previous_adsl_status
    print("DEBUG: Entering check_snmp_status function...")

    while True:
        status = await get_adsl_status(5) # Here 2 seconds delay is used for illustration. Adjust as needed.
        if READY in status:
            print("DEBUG: ADSL status is READY.")
            await lights_on(254)
            await set_colour("green")
        elif TRAINING in status:
            print("DEBUG: ADSL status is TRAINING.")
            await lights_on(127)
            await set_colour("yellow")
        elif SHOWTIME in status and (previous_adsl_status == "REDAY" or previous_adsl_status == "TRAINING"):
            print("DEBUG: ADSL status is SHOWTIME after being READY or TRAINING.")
            await lights_on(254)
            await set_colour("green")
            asyncio.create_task(slowly_dim_lights())
            previous_adsl_status = "SHOWTIME"
        else:
            print("DEBUG: ADSL status is unknown or SHOWTIME without prior READY/TRAINING.")
            await lights_off()
            if SHOWTIME in status:
                previous_adsl_status = "SHOWTIME"
                
        await asyncio.sleep(10)  # Check every 10 seconds. Adjust as needed.
    print("DEBUG: Exiting check_snmp_status function.")

async def ping_device():
    print("DEBUG: Entering ping_device function...")
    proc = subprocess.Popen(["ping", "-c", "1", SNMP_TARGET_HOST], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate()
    print(f"DEBUG: Ping result: {proc.returncode == 0}")
    return proc.returncode == 0

#=======#
# START #
#=======#

print("DEBUG: Starting script...")

# Check if the API key file exists
if os.path.exists(API_KEY_FILE_NAME):
    # Fetch the API key from the key file
    with open(API_KEY_FILE_NAME, 'r') as keyfile:
        API_KEY = keyfile.read()
else:
    print(f"ERROR: File '{API_KEY_FILE_NAME}' does not exist!")
    exit(1)

# Check whether the snmpget command is existing
if not which(SNMP_GET_CMD):
    print("ERROR: snmpget command not found!")
    exit(1)

# Construct the snmpget command
snmpget_cmd = [SNMP_GET_CMD, SNMP_VERSION_OPT, SNMP_VERSION, SNMP_RETRY_OPT, SNMP_RETRY_COUNT, SNMP_COMMUNITY_OPTION, SNMP_COMMUNITY, SNMP_TARGET_HOST, SNMP_OID]

asyncio.run(check_snmp_status())

print("DEBUG: Script finished.")