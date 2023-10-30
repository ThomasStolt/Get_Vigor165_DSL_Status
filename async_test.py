# this approach has been given up, it does not seem that asyncio is a good fit for this use case

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
FIRST_RUN = True

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
    print("DEBUG: Entering get_adsl_status...")
    await asyncio.sleep(delay)
    
    process = subprocess.Popen(snmpget_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = process.communicate()
    
    if stderr_data:
        await set_colour("red")
        await lights_on(254)
        
        # ICMP ping loop
        while not await ping_device():
            await asyncio.sleep(5)
            
        # Retry getting SNMP status
        process = subprocess.Popen(snmpget_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = process.communicate()
    
    status = stdout_data.decode().strip()
    return status


async def check_snmp_status():
    global previous_adsl_status
    global FIRST_RUN
    status = await get_adsl_status(0)
    while True:
        
        if READY in status:
            asyncio.create_task(blink_lights("red", 1))
            previous_adsl_status = "READY"

        elif TRAINING in status:
            asyncio.create_task(blink_lights("yellow", 1))
            previous_adsl_status = "TRAINING"

        elif SHOWTIME in status:
            if FIRST_RUN:
                FIRST_RUN = False
                await lights_on(0)
                await set_colour("green")
                await lights_off()
                for _ in range(3):  # Blink 3 times initially
                    print("DEBUG: Blinking 3 times green...")
                    await lights_on(254)
                    await asyncio.sleep(2)
                    await lights_off()
                    await asyncio.sleep(2)

            if previous_adsl_status in ["READY", "TRAINING"]:
                await lights_on(254)
                await set_colour("green")
                asyncio.create_task(slowly_dim_lights())
                previous_adsl_status = "SHOWTIME"
            else:
                await lights_off()
                previous_adsl_status = "SHOWTIME"
        
        else:
            await lights_off()

        status = await get_adsl_status(5)


async def ping_device():
    print("DEBUG: Entering ping_device function...")
    proc = subprocess.Popen(["ping", "-c", "1", SNMP_TARGET_HOST], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate()
    print(f"DEBUG: Ping result: {proc.returncode == 0}")
    return proc.returncode == 0

async def blink_lights(colour, duration):
    await set_colour(colour)
    while True:
        await lights_on(254)
        await asyncio.sleep(duration)
        await lights_off()
        await asyncio.sleep(duration)


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
