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

## Install and setup companion

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

echo ""
echo "INFO: Install is now complete. Please reboot and make sure everything is working as expected"
echo ""

exit 0

