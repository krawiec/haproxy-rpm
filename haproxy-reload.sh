#!/bin/bash

declare -a sockets_array=( $(ls /var/run/haproxy*.sock) )

for  i in "${!sockets_array[@]}";
do
	echo "show servers state" | socat unix-connect:${sockets_array[i]} stdio >> /var/lib/haproxy/server-state
done

systemctl reload-or-restart haproxy

sleep 2
truncate --size=0 /var/lib/haproxy/server-state
