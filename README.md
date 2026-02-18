# sony-ptz-demo
Simple webUI for setting up camera(s)

# USB
sudo apt install libhidapi-libusb0 libxcb-cursor0
sudo sh -c 'echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"0fd9\", TAG+=\"uaccess\"" > /etc/udev/rules.d/70-streamdeck.rules'
sudo sh -c 'echo "SUBSYSTEM==\"hidraw\", ATTRS{idVendor}==\"0fd9\", TAG+=\"uaccess\"" >> /etc/udev/rules.d/70-streamdeck.rules'
sudo udevadm control --reload-rules
sudo udevadm trigger

# Docker
docker pull ghcr.io/bitfocus/companion/companion:4.2.4-8798-stable-f844bbb4fc
docker run -d --privileged -p 10000:8000 --name "Companion" -v /dev/hidraw0:/dev/hidraw0 7cefa059e80e
