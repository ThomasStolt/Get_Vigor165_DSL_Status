#!/bin/bash

# Define the IP range
start_ip=1
end_ip=20

# Perform the ping loop
for ((i = $start_ip; i <= $end_ip; i++)); do
    ip="192.168.2.$i"
    ping -c 1 "$ip" &>/dev/null
    if [ $? -eq 0 ]; then
        echo "$ip is reachable"
    else
        echo "$ip is not reachable"
    fi
done

