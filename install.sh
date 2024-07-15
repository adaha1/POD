#!/bin/bash

if [["$EUID" != 0]]; then
    sudo -k
    echo "Please enter sudo password"
    if sudo true; then
        echo "Initializing install"
    else
        echo "Wrong Password. Exiting..."
        exit 1
    fi
fi

# Check for and install general updates
sudo apt update && sudo apt upgrade -y

# Install python and pip if not installed
sudo apt install python3 python3-pip

# Install python module RPi.GPIO
python3 -m pip install RPi.GPIO

# Install python module board
python3 -m pip install board

# Install python module adafruit-blinka
python3 -m pip install adafruit-blinka

# Install python module ads1x15 for ADC
python3 -m pip install adafruit-circuitpython-ads1x15