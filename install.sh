#!/bin/bash

# halt on errors
set -e

sudo apt-get update

sudo apt-get install python3-pip virtualenv python3-dev python3-tk libfreetype6-dev \
    screen g++ python-tk unzip libsnappy-dev cmake -qq

#default tor install
sudo apt-get install tor -qq

git pull

#configs files
if [ ! -f config/containers.cfg ]; then
    cp config/containers.cfg.sample config/containers.cfg
fi
if [ ! -f config/proxies_profiles.cfg ]; then
    cp config/proxies_profiles.cfg.sample config/proxies_profiles.cfg
fi


pip3 install -U pip
pip3 install -U -r requirements.txt

pushd gen_cert
./gen_root.sh
wait
./gen_cert.sh
wait
popd

cp gen_cert/server.crt ${AIL_FLASK}/server.crt
cp gen_cert/server.key ${AIL_FLASK}/server.key
