# sony-ptz-demo
Simple webUI for setting up camera(s)

# USB
sudo apt install libhidapi-libusb0 libxcb-cursor0
sudo sh -c 'echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"0fd9\", TAG+=\"uaccess\"" > /etc/udev/rules.d/70-streamdeck.rules'
sudo sh -c 'echo "SUBSYSTEM==\"hidraw\", ATTRS{idVendor}==\"0fd9\", TAG+=\"uaccess\"" >> /etc/udev/rules.d/70-streamdeck.rules'
sudo udevadm control --reload-rules
sudo udevadm trigger

# Docker

# Add Docker's official GPG key:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

# Companion
Companion docker page: https://github.com/bitfocus/companion/pkgs/container/companion%2Fcompanion

Create local companion dir
sudo mkdir -p /companion
sudo chmod 777 /companion

sudo docker pull ghcr.io/bitfocus/companion/companion:latest
sudo docker run -d --privileged -p 10000:8000 -v /companion:/companion --name "Companion" -v /dev/hidraw0:/dev/hidraw0 --restart always ghcr.io/bitfocus/companion/companion:latest


$ cat ~/.config/labwc/autostart
chromium --noerrdialogs --disable-infobars --no-first-run --enable-features=OverlayScrollbar --start-maximized http://localhost:8080 &
