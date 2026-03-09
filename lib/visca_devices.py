from curses.ascii import NAK
import sys
import ipaddress
from visca_discovery import VISCA_DEVICES

net4 = ipaddress.ip_network('192.168.111.0/24')
first_host = 11


def find_visca_devices():
    ## Visca discovery
    my_visca = VISCA_DEVICES(ip="255.255.255.255", port=52380, verbose=5)
    visca_list = my_visca.get_visca_devices()
    my_visca.close_connection()

    VISCA_LIST = []
    
    if isinstance(visca_list, list):
        for visca in visca_list:
            if "IPADR" in visca and "MAC" in visca:
                if visca["WRITE"] == 'off':
                    print(f"MAC: {visca['MAC']} IP: {visca['IPADR']}")
                    VISCA_LIST.append(visca)
                else:
                    print(f"VISCA device with MAC:{visca['MAC']} and NAME:{visca['NAME']} found but not writable. Skipping!")
            else:
                print(f"The item did not contain the expected keys: {visca}")
    else:
        print("No VISCA devices found. Aborting!")
        sys.exit(1)
    return VISCA_LIST

def main():
    visca_devices = find_visca_devices()
    print(f"Discovered VISCA devices: {visca_devices}")
    host_ip = first_host
    
    for device in visca_devices:
        print()
        print(f"Camera MAC Address: {device['MAC']}")
        my_visca = VISCA_DEVICES(ip="255.255.255.255", port=52380, verbose=5)
        visca = my_visca.set_visca_device_ip(device_mac=device['MAC'], device_ip=f"{net4[host_ip]}", device_mask=net4.netmask, device_gateway=net4[1], device_name=f"Peter")
        if "NAK" in visca[0]:
            print(f"Failed to set IP for device with MAC {device['MAC']}. Response: {visca}")
        else:
            print(visca)
        my_visca.close_connection()
        host_ip += 1





    # my_cam = Camera(ip=visca['IPADR'], verbose=5)

    # # my_cam.recall_preset1()
    # # time.sleep(2)
    # # my_cam.recall_preset2()
    # # time.sleep(2)
    # my_cam.pantilt(pan_position=8704, pan_speed=20, tilt_position=0, tilt_speed=20, relative=False)

    # time.sleep(5)
    # position = my_cam.get_pantilt_position()
    # print(f"Current Pan-Tilt Position: {position}")

if __name__ == "__main__":
    main()
    #print(f"IP: {net4[100]} Mask: {net4.netmask} Gateway: {net4[1]}")
    sys.exit(0)
    