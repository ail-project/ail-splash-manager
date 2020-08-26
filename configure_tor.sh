#!/bin/bash

# halt on errors
set -e

sudo sed -i 's/#SOCKSPolicy accept 192.168.0.0\/16/SOCKSPolicy accept 172.17.0.0\/16/1' /etc/tor/torrc
wait
sudo sed -i 's/#SOCKSPort 192.168.0.1:9100/SOCKSPort 0.0.0.0:9050/1' /etc/tor/torrc
wait

# restart tor proxy
sudo service tor restart
