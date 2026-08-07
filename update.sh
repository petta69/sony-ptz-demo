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


## Start the virtual environment
VIRTUAL_ENV="$CONTROLLER_HOME/.venv"
export VIRTUAL_ENV
source $VIRTUAL_ENV/bin/activate

## Update git
git reset --hard HEAD
/usr/bin/git pull

## Restart services to apply new files
systemctl --user restart sony-ptz-demo.service

##
## Update docker image for companion
##

container_id=$(sudo docker ps -q --filter "name=Companion")
if [ -n "$container_id" ]
then
    echo "INFO: Stopping and removing existing companion container"
    sudo docker stop Companion
    sudo docker rm Companion

    image_id=$(sudo docker images -q ghcr.io/bitfocus/companion/companion:latest)
    if [ -n "$image_id" ]
    then
        echo "INFO: Removing existing companion image"
        sudo docker rmi ghcr.io/bitfocus/companion/companion:latest
        echo "INFO: Finished removing existing companion image"
    fi
fi

image_id=$(sudo docker images -q ghcr.io/bitfocus/companion/companion:latest)
if [ ! -n "$image_id" ]
then
    echo "INFO: No existing companion image found"
    echo "INFO: Pulling latest companion image"
    sudo docker pull ghcr.io/bitfocus/companion/companion:latest
    sudo docker run -d --privileged -p 10000:8000 -v /companion:/companion --name "Companion" -v /dev/hidraw0:/dev/hidraw0 --restart always ghcr.io/bitfocus/companion/companion:latest
    container_id=$(sudo docker ps -q --filter "name=Companion")
    if [ -n "$container_id" ]
    then
        echo "INFO: Successfully started companion container"
    else
        echo "ERROR: Failed to start companion container"
        exit 10
    fi
fi


echo ""
echo "Update complete...."
echo ""

exit 0
