# Get Vigor 165 DSL Status

If internet connectivity in your home goes down, it is often difficult to find out why: is it the WiFi? Is it the DSL connection? Is it your phone that has lost the WiFi connection? Or a myriad of other reasons.

For me, my DSL router looses connectivity every so often. When then happens, it takes about a minute or so, until it has renegotiated the connection speed with its head end at the Service Provider. I wanted something that immideately shows, that the DSL connection is down. Luckily, I have many Hue lights at home, specifically some Hue Play Lights, that I don't have a real use for anymore. So I decide to use them as "DSL status lights". The the DSL connection goes down, it will turn those lights red! If the DSL router is in the negotiation ("Training") phase, the lights will turn yellow and if the connection is re-established, the lights will turn green, slowly fading out.

Luckily the DrayTek Vigor routers speak SNMP, via which it is easy to find out, which connection state a router is currently in, which this tool is using.

So, I created a systemd service that does that and can run on a RaspberryPi. This tool will monitor the online status of your DrayTek (Vigor 165) and indicate the status via a set of Hue lights:


- Red (solid)
  - no connection to the Vigor, e. g. rebooting
- Red  (flashing fast)
  - DSL disconnected
- Yellow (flashing slowly)
  - Vigor is trying to establisha DSL connection
- Green (slowly fading out)
  - DSL connection is established, you are connected!

## Prerequisites

### Required hardware

1. Draytek Vigor DSL Router. At this point, the only tested model ist Vigor 165.
2. Philips Hue lights with HueBridge, all connected and working.
3. A linux system to hosts this tool. As mentioned, a Raspberry Pi will do.

### Software

Make sure your networking is all set up and that the device hosting this script can ping the router and the Hue bridge. Switch on SNMP on your router and test the connectivity from your host using the following command. You will need to install net-snmp for this to work:

```console
pi@raspberry-pi:~ % snmpgetnext -v 1 -r 0 -c public <router_IP_address> .1.3.6.1
```

You should receive a response, something like this:

```console
SNMPv2-MIB::sysDescr.0 = STRING: DrayTek Corporation, Router Model: Vigor165, Version: 4.2.3.1_STD...
```

If you get an error it might be helful to try nmap for basic connectivity checking. Simply use the "-sU" flag to tell nmap to scan UDP ports (SNMP is UDP, not TCP) and you likely need to use sudo:

```console
pi@raspberry-pi:~ % sudo nmap -sU <router_IP_address>
Starting Nmap 7.93 ( https://nmap.org ) at 2023-04-29 10:12 CEST
Nmap scan report for <router_IP_address>
Host is up (0.037s latency).
Not shown: 999 open|filtered udp ports (no-response)
PORT    STATE SERVICE
161/udp open  snmp    *<-- this is what you are looking for!!!*
MAC Address: 00:1D:AA:XX:XX:XX (DrayTek)
Nmap done: 1 IP address (1 host up) scanned in 23.93 seconds
```

## Configuration

You will need to edit the following DEFINITIONS in Get_Vigor165_DSL_Status.py:

Replace this string with the IP address or hostname of your Hue Bridge:

```HUE_BRIDGE_IP = "PhilipsHueBridge"```

Get your Philips API key (either here: [https://developers.meethue.com/develop/get-started-2/](https://developers.meethue.com/develop/get-started-2/) or, if that address has changed you have to google for it).

Rename `` Philips_Hue_API_Key.txt.example `` to `` Philips_Hue_API_Key.txt `` and put your API key in it. This file needs to be found by the adsl_config.sh script, just use the same directory.

```API_KEY_FILE_NAME = "Philips_Hue_API_Key.txt"```



```GROUP_NR = "17"```

This is the group of Hue lights, that you want this script to control. At this point, this script has only been tested with "Hue Play" light bars. A simple way of finding out which groups you have is using this request in a browser pointing towards your Hue bridge:

``` http://philipshuebridge/api/<your_API_key>/groups/ ```

but that is hard to read. If you are using command line, you can use this:

```console
curl -s http://<Hue_bridge_IP_address>/api/<your_API_key>/groups/ | jq .| grep -E '"[0-9]+": {|"name":'
```

You might need to install jq first. That will list the groups number (usually rooms) of your lights followed by their respective names for easier identification.

## Installation

After you configured everthing in the configuration steps above, run the shell script adsl_config.sh with sudo. That script takes one out of three arguments like so:

```console
adsl_config.sh --check
```

this checks whether this tool is already installed as a systemd service

```console
adsl_config.sh --install
```

this takes the following steps:

- creates a user "adsl_monitor" for the systemd service
- installs the systemd service "adsl_monitoring.service"
- copies the Python script "Get_Vigor165_DSL_Status.py to /usr/local/bin
- copies the Philips_Hue_API_Key.txt to /etc/adsl_monitoring/

```console
adsl_config.sh --remove
```

- removes everything that has been installed by ``` --install ```

After you have done the ```--install``` above, you should have a service running. If all goes well, your lights should turn green and slowly dimm down over the next 5 minutes or so. If they turn red, then there is a connectivity issue. In that case check the steps above.

## What the Colours mean

- Solid Red
  - The Router cannot be contacted, likely the router is off or rebooting, or you have a networking issue.
- Fast Blinking Red
  - "READY" mode => The DSL connection is disconnected and has not yet begun negotiating the connection speed
- Slow Blinking Red
  - "TRAINING" mode => Router is currently negotiation the DSL speed with its counterpart at your service provider
- Solid Green (slowly dimming)
  - "SHOWTIME" mode => Router has connected to the Service Provider and has negotiated a speed, this equals "normal operation". The green light will slowly be dimmed until it is completely switched off.

## How does this scrip work exaactly?

We use SNMP to poll the status of the DSL Connection from the router using the following command:

```console
snmpget -v 1 -r 0 -c public <router_IP> .1.3.6.1.2.1.10.94.1.1.3.1.6.4
```

this will query an SNMP MIB attribute called "adslAturCurrStatus" from the router, the returned value is a string containing a set of octets representing the connection status of the router. We do some simple string matching as follows:

If the string contains the following numbers, we are in SHOWTIME:

53 48 4F 57 54 49 4D 45 it means:

S  H  O  W  T  I  M  E

For TRAINING mode the numbers are this:

54 52 41 49 4E 49 4E 47 

T  R  A  I  N  I  N  G

And lastly for READY, the numbers are this:

52 45 41 44 59
R  E  A  D  Y

There is also a FAIL state, not sure when exactly this occurs, but in the get_adsl_status function this (and any other values) will be ignored.
