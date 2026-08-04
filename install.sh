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


sudo apt -y install virtualenv
virtualenv .venv

## Start the virtual environment
VIRTUAL_ENV="$CONTROLLER_HOME/.venv"
export VIRTUAL_ENV
source $VIRTUAL_ENV/bin/activate

## Install python modules:
python3 -m pip install --upgrade pip
if [ -f requirements.txt ] 
then
    python3 -m pip install -r requirements.txt
else
    echo "ERROR: Could not find required file"
    exit 10    
fi

## Install udev rules for Stream Deck
if [ -f /etc/udev/rules.d/70-streamdeck.rules ]
then
    echo "INFO: Already have udev rules for Stream Deck"
else
    echo "INFO: Installing udev rules for Stream Deck"

    sudo apt -y install libhidapi-libusb0 libxcb-cursor0
    sudo sh -c 'echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"0fd9\", TAG+=\"uaccess\"" > /etc/udev/rules.d/70-streamdeck.rules'
    sudo sh -c 'echo "SUBSYSTEM==\"hidraw\", ATTRS{idVendor}==\"0fd9\", TAG+=\"uaccess\"" >> /etc/udev/rules.d/70-streamdeck.rules'
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

##
## Add docker repo and install docker
##

## Install docker keyring and add docker repository to apt sources
if [ -f /etc/apt/keyrings/docker.asc ]
then
    echo "INFO: Already have docker keyring"
else
    echo "INFO: Installing docker keyring"

    sudo apt update
    sudo apt -y install ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
fi

if [ -f /etc/apt/sources.list.d/docker.sources ]
then
    echo "INFO: Already have docker sources"
else
    echo "INFO: Adding docker sources"
    # Add the repository to Apt sources:
    sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
fi

## Install docker
sudo apt update
sudo apt -y install docker.io
sudo systemctl enable docker
sudo systemctl start docker

##
## Install and setup companion
##

## Create shared directory for companion
sudo mkdir -p /companion
sudo chmod 777 /companion

$RSYNC -av $CONTROLLER_HOME/companion_dir.tar /companion/
cd /companion
if [ -f companion_dir.tar ]
then
    tar -xf companion_dir.tar
    rm companion_dir.tar
fi

## Pull and run companion docker image
sudo docker pull ghcr.io/bitfocus/companion/companion:latest
sudo docker run -d --privileged -p 10000:8000 -v /companion:/companion --name "Companion" -v /dev/hidraw0:/dev/hidraw0 --restart always ghcr.io/bitfocus/companion/companion:latest


## Bootstrap (For the webserver part)
cd $CONTROLLER_HOME/static
if [ -f bootstrap-5.3.3-dist.zip ]
then
    echo "INFO: Already have bootstrap file"
else
    wget https://github.com/twbs/bootstrap/releases/download/v5.3.3/bootstrap-5.3.3-dist.zip
fi
if [ -d bootstrap ]
then
    echo "INFO: Already have bootstrap dir"
else
    bootstrap_file=$(find -type f -name "bootstrap*.zip")
    unzip $bootstrap_file
    bootstrap_dir=$(find -type d -name "bootstrap*")
    ln -s $bootstrap_dir bootstrap
fi

## Copy default files
$RSYNC -av $CONTROLLER_HOME/system/install/start_sony-ptz-demo.sh $CONTROLLER_HOME/
$RSYNC -av $CONTROLLER_HOME/system/install/sony-ptz-demo.service $CONTROLLER_HOME/system/


## Set correct CONTROLLER_HOME variable in startup script
cd $CONTROLLER_HOME
if [ -f start_sony-ptz-demo.sh ]
then
    sed -i "s|REPLACE|$CONTROLLER_HOME|g" start_sony-ptz-demo.sh
fi

## Same thing for the service scripts
if [ -f system/sony-ptz-demo.service ]
then
    sed -i "s|REPLACE|$CONTROLLER_HOME|g" system/sony-ptz-demo.service
fi


## Now prepare dir for user service script
if [ ! -d $HOME/.local/share/systemd/user/default.target ]
then
	mkdir -p $HOME/.local/share/systemd/user/default.target
fi

sudo ln -s $CONTROLLER_HOME/system/sony-ptz-demo.service /usr/lib/systemd/user/ 
systemctl --user daemon-reload
systemctl --user enable sony-ptz-demo
systemctl --user start sony-ptz-demo

## Set wallpaper
/usr/bin/pcmanfm --set-wallpaper="source/sony-ptz-demo/images/SONY_WhiteOnBlack.png" --display=:0

if [ -f ~/.config/labwc/autostart ]
then
    echo "INFO: Already have autostart file"
else
    echo "INFO: Creating autostart file"
    mkdir -p ~/.config/labwc
    echo "chromium --noerrdialogs --disable-infobars --no-first-run --enable-features=OverlayScrollbar --start-maximized http://localhost:8080 &" > ~/.config/labwc/autostart
fi

echo ""
echo "INFO: Install is now complete. Please reboot and make sure everything is working as expected"
echo ""

exit 0

