# sony-ptz-demo
Simple webUI for setting up camera(s)

# USB
sudo apt install libhidapi-libusb0 libxcb-cursor0
sudo sh -c 'echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"0fd9\", TAG+=\"uaccess\"" > /etc/udev/rules.d/70-streamdeck.rules'
sudo sh -c 'echo "SUBSYSTEM==\"hidraw\", ATTRS{idVendor}==\"0fd9\", TAG+=\"uaccess\"" >> /etc/udev/rules.d/70-streamdeck.rules'
sudo udevadm control --reload-rules
sudo udevadm trigger

# Docker
Companion docker page: https://github.com/bitfocus/companion/pkgs/container/companion%2Fcompanion

docker pull ghcr.io/bitfocus/companion/companion:4.2.5-8815-stable-8821dfa519
docker run -d --privileged -p 10000:8000 --name "Companion" -v /dev/hidraw0:/dev/hidraw0 --restart always ghcr.io/bitfocus/companion/companion:4.2.5-8815-stable-8821dfa519
