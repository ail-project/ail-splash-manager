#!/bin/bash

RED="\\033[1;31m"
DEFAULT="\\033[0;39m"
GREEN="\\033[1;32m"
WHITE="\\033[0;02m"

if [ "$EUID" -ne 0 ]; then
    echo -e $RED"\t* Please run as root or sudo.\n"$DEFAULT
    exit 1
fi

issplashed=`sudo screen -ls | egrep '[0-9]+.AIL_Splash_Manager' | cut -d. -f1`

usage() { echo "Usage: sudo $0" 1>&2;
          echo "          -l: Launch AIL Splash Manager";
          echo "          -k: Kill AIL Splash Manager";
          echo "";
          echo "example:";
          echo "sudo ./launch.sh -l";
          exit 1;
        }

#If no params, display the help
[[ $@ ]] || {
    usage;
}

function launch_manager {
    if [[ $issplashed ]]; then
        echo -e $RED"\t* A screen is already launched, please kill it before creating another one."$DEFAULT
        exit 1
    fi

    screen -dmS "AIL_Splash_Manager"
    sleep 0.1
    screen -S "AIL_Splash_Manager" -X screen -t "Flask" bash -c 'sudo ./Flask_server.py; read x'
    sleep 0.1
    printf "$GREEN    AIL Splash Manager launched\n"
}

function kill_manager {
    if [[ $issplashed ]]; then
        echo -e $GREEN"Killing AIL Splash Manager"$DEFAULT
        kill $issplashed
        sleep 0.2

        sudo ./splash_manager.py -k

        echo -e $ROSE`sudo screen -ls`$DEFAULT
        echo -e $GREEN"\t* $issplashed killed."$DEFAULT

    else
        echo -e $RED"\t* No screen to kill"$DEFAULT
    fi
}

while [ "$1" != "" ]; do
    case $1 in
      -l)
          launch_manager;
          ;;
      -k)
          kill_manager;
          ;;
      *)
          usage
          ;;
    esac
    shift
done
