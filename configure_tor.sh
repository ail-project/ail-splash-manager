#!/bin/bash

# halt on errors
set -e

# sudo sh -c 'echo "deb https://deb.torproject.org/torproject.org $(lsb_release -sc) main" >> /etc/apt/sources.list.d/tor-project.list'

sudo sed -i 's/#SocksPolicy accept 192.168.0.0\/16/SocksPolicy accept 172.17.0.0\/16/1' /etc/tor/torrc
wait
sudo sed -i 's/#SocksPort 192.168.0.1:9100/SocksPort 0.0.0.0:9050/1' /etc/tor/torrc
wait

# restart tor proxy
sudo service tor restart
