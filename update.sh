#!/bin/bash -x

## Make sure we use the display of logged in user
export DISPLAY=:0
export CONTROLLER_HOME=$PWD
cd $CONTROLLER_HOME

RSYNC=/usr/bin/rsync

## Turn off screensaver and blanking
xset -dpms
xset s off

## First make sure system is up to date
sudo apt update && sudo apt -y upgrade && sudo apt -y autoremove

## Prepare python env
sudo apt -y install virtualenv
virtualenv .venv

## Start the virtual environment
VIRTUAL_ENV="$CONTROLLER_HOME/.venv"
export VIRTUAL_ENV
source $VIRTUAL_ENV/bin/activate

## Update git
/usr/bin/git pull

## Restart services to apply new files
systemctl --user restart sony-ptz-demo.service

echo ""
echo "Update complete...."
echo ""

exit 0
