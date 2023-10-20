# Get Vigor 165 DSL Status

This program will monitor the online status of your DrayTek (Vigor 165) and indicate the status via a set of Hue lights:


- Red (solid)
  - no connection to the Vigor, e. g. rebooting
- Red  (flashing fast) -> DSL disconnected
- Yellow (flashing slow) -> Vigor is trying to establisha DSL connection
- Green (slowly fading out) -> DSL connection is established, you are connected

## Prerequisites

### Required hardware

1. Draytek Vigor DSL Router (at this point, the only tested model ist Vigor 165)
2. Philips Hue lights with HueBridge, all connected and working
3. A linux system to hosts this tool (a Raspberry Pi will do)

### Software

Make sure your networking is all set up and that the device hosting this script can ping the router and the Hue bridge. Switch on SNMP on your router and test the connectivity from your host using the following command. You will need to install net-snmp for this to work:

pi@raspberry-pi:~ % snmpgetnext -v 1 -r 0 -c public <router_IP_address> .1.3.6.1

You should receive a response, something like this:

SNMPv2-MIB::sysDescr.0 = STRING: DrayTek Corporation, Router Model: Vigor165, Version: 4.2.3.1_STD...

If you get an error and connot find out why, you can try nmap for
basic connectivity checking. You need to use the "-sU" flag to tell
# nmap to scan UDP ports (SNMP is UDP, not TCP) and you likely need to
# use sudo:
#
# pi@raspberry-pi:~ % sudo nmap -sU <router_IP_address>
# Starting Nmap 7.93 ( https://nmap.org ) at 2023-04-29 10:12 CEST
# Nmap scan report for <router_IP_address>
# Host is up (0.037s latency).
# Not shown: 999 open|filtered udp ports (no-response)
# PORT    STATE SERVICE
# 161/udp open  snmp    <-- this is what you are looking for!!!
# MAC Address: 00:1D:AA:XX:XX:XX (DrayTek)
#
# Nmap done: 1 IP address (1 host up) scanned in 23.93 seconds
#
#
# Configuration
# =============
#
# You will need to edit the following DEFINITIONS in Get_Vigor165_DSL_Status.py:
#
# HUE_BRIDGE_IP = "PhilipsHueBridge"
# Replace this string with the IP address or hostname of YOUR Hue Bridge
#
# API_KEY_FILE_NAME = "Philips_Hue_API_Key.txt"
# Rename the Philips_Hue_API_Key.txt.example by removing ".example" and put
# your API key in it. This file needs to be found by the adsl_config.sh
# script, just use the same directory.
#
# GROUP_NR = "17"
# This is the group of Hue lights, that you want this script to control.
# At this point, this script has only been tested with "Hue Play" light bars.
# A simple way of finding out which groups you have is using this
# request in a browser pointing towards your Hue bridge:
# http://philipshuebridge/api/<your_API_key>/groups/
# but that is hard to read. If you are using command line, you can use this:
#
# curl -s http://<Hue_bridge_IP_address>/api/<your_API_key>/groups/ | jq .| grep -E '"[0-9]+": {|"name":'
#
# You might need to install jq first. That will list the numbers of your
# lights followed by their respective names for easier identification.
#
#
# Installation
# ============
#
# After you configured everthing in the Configuration step above, run the shell
# script adsl_config.sh with sudo. That script takes one argument like so:
# --check   - checks whether this tool is already installed as a systemd service
# --install - creates a user "adsl_monitor" for the systemd service
#             installs the systemd service "adsl_monitoring.service"
#             copies the Python script "Get_Vigor165_DSL_Status.py to /usr/local/bin
#             copies the Philips_Hue_API_Key.txt to /etc/adsl_monitoring/
# --remove  - removes everything that has been installed by --install
#
# After you have done the --install above, you should have a service running.
# If all goes well, your lights should turn green and slowly dimm down over the
# next 10 minutes or so. If they turn red, then there is a connectivity issue.
# In that case check the steps above.
#
#
# What the Colours mean
# =====================
#
# Solid Red
# ---------
# The Router is not available, likely the router is off or rebooting, or
# you have a networking issue.
#
# Fast Blinking Red
# -----------------
# "READY" mode => The DSL connection is disconnected and has not yet begun
# negotiating the connection speed
# 
# Slow Blinking Red
# -----------------
# "TRAINING" mode => Router is currently negotiation the DSL speed with its
# counterpart at your service provider
#
# Solid Green (slowly dimming)
# ----------------------------
# "SHOWTIME" mode => Router has connected to the Service Provider and
# has negotiated a speed, this equals "normal operation". The green light
# will slowly be dimmed until it is completely switched off.
#
# We use SNMP to pull the status of the DSL Connection from the router
# using the following command:
# snmpget -v 1 -r 0 -c public <router_IP> .1.3.6.1.2.1.10.94.1.1.3.1.6.4
# this will query the adslAturCurrStatus attribute from the router, the
# returned value is a string, containing a set of octets, representing
# then status of the router. We do some simple string matching as follows:
#
# If the string contains the following numbers, we are in SHOWTIME:
# 53 48 4F 57 54 49 4D 45
# S  H  O  W  T  I  M  E
#
# For TRAINING mode the numbers are this:
# 54 52 41 49 4E 49 4E 47 
# T  R  A  I  N  I  N  G
#
# And lastly for READY, the numbers are this:
# 52 45 41 44 59
# R  E  A  D  Y
#
# There is also a FAIL state, not sure when exactly this occurs, but in the
# get_adsl_status function this (and any other values) will be ignored
#
#==============================================================================#
