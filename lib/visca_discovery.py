import socket
import time
from typing import Optional, Tuple
import logging
import sys
import traceback

logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(fmt=('[%(levelname)s] %(name)s ''%(funcName)s | %(message)s')))
logger.handlers = [handler]
logger.setLevel('DEBUG') # or INFO, or DEBUG, etc
logger = logging.getLogger(__name__)

class VISCA_DEVICES:
    def __init__(self, ip: str, port=52380, verbose=1):
        self._location = (ip, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # for UDP stuff
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Try to bind to the specified port. If it fails, print an error and exit.
        try:
            self._sock.bind(('', port))
        except socket.error as err:
            logger.error(f"Failed to bind to port {port}: {err}")
            # self._sock.close()
            # sys.exit(1)
            pass
        self._port = self._sock.getsockname()[1]
        self._sock.settimeout(2)
        
        self.num_missed_responses = 0
        self.num_retries = 5

    def _send_command(self, command_hex: str, setIP=False):
        if setIP == True:
            payload_bytes = command_hex
        else:
            preamble = b'\x02'
            terminator = b'\xff\x03'
            payload_bytes = preamble + bytearray.fromhex(command_hex) + terminator

        exception = None
        for retry_num in range(self.num_retries):
            message = payload_bytes

            logger.debug(f"Sending: {message} Location: {self._location} Socket: {self._sock.getsockname()}")
            self._sock.sendto(message, self._location)
            logger.debug(self._sock)
            response = None # Set default response to None before trying to receive it

            response = self._listen_udp_broadcast_with_timeout(data_in=message, timeout_seconds=1, verbose=5)
            if response is not None:
                logger.debug(f"Response: {response}")
                return response

           
            if response is None:
                logger.debug("Response is None")
                #return response[1:-1]
                return

        if exception:
            raise exception
        else:
            logger.error("No response after retries")


    def _listen_udp_broadcast_with_timeout(self, data_in=None, timeout_seconds=5, verbose=5):
        # Set the timeout for blocking socket operations
        self._sock.settimeout(timeout_seconds)

        data_list = []
        data_dict = {}

        while True:
            try:
                # Wait to receive data
                data, address = self._sock.recvfrom(4096)
                if data_in == data:
                    logger.debug("Received our own message, ignoring.")
                    continue
                else:
                    logger.debug(f"Received {len(data)} bytes from {address}")
                    data = data[1:-2]
                    data = data.replace(b'\xff', b'\n')
                    data_string = data.decode('utf-8')
                    logger.debug(f"Data: {data_string}")
                    ## create dictionary from response                    
                    for line in filter(None, data_string.strip().split('\n')):
                        # Split each line by the first colon
                        try:
                            key, value = line.split(':', 1)
                            ## Filter out ENQ response
                            if key.strip() == "ENQ":
                                logger.debug("Received ENQ response, ignoring.")
                                continue
                            data_dict[key.strip()] = value.strip()
                        except Exception:
                            # Handle lines that might not have a colon if necessary
                            logger.error(f"Skipping line due to incorrect format: {line}")
                
                    if data_dict:
                        data_list.append(data_dict)

                    data_dict = {}

            except socket.timeout:
                logger.debug(f"Timeout: No data received within {timeout_seconds} seconds.")
                break
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                traceback.print_exc()
                continue
        return data_list


    def close_connection(self):
        self._sock.close()    


    def get_visca_devices(self) -> str:
        command_data = "ENQ:network".encode("utf-8").hex()

        response = self._send_command(command_hex=command_data, setIP=False)
        self.close_connection()

        if response is None:
            logger.error('ERROR: Could not find any devices')
            return {"ERROR": "Could not find any devices"}
        else:
            return response
                                                                                                                                
    def set_visca_device_ip(self, device_mac: str, device_ip: str, device_mask: str, device_gateway: str, device_name: str) -> None:
        preamble = b'\x02'
        terminator = b'\xff\x03'
        filler = b'\xff'
        cam_mac = f"MAC:{device_mac}".encode("utf-8").hex()
        cam_ip = f"IPADR:{device_ip}".encode("utf-8").hex()
        cam_mask = f"MASK:{device_mask}".encode("utf-8").hex()
        cam_gateway = f"GATEWAY:{device_gateway}".encode("utf-8").hex()
        cam_name = f"NAME:{device_name}".encode("utf-8").hex()
        
        command_data = preamble + bytearray.fromhex(cam_mac) + filler + bytearray.fromhex(cam_ip) + filler + bytearray.fromhex(cam_mask) + filler + bytearray.fromhex(cam_gateway) + filler + bytearray.fromhex(cam_name) + terminator

        response = self._send_command(command_hex=command_data, setIP=True)

        if response is None:
            logger.error('ERROR: Could not set device IP address')
            return {"ERROR": "Could not set device IP address"}
        else:
            return response

##
## Exception classes
##

class ViscaException(RuntimeError):
    """Raised when the camera doesn't like a message that it received"""

    def __init__(self, response_body):
        self.status_code = response_body[2]
        descriptions = {
            1: 'Message length error',
            2: 'Syntax error',
            3: 'Command buffer full',
            4: 'Command cancelled',
            5: 'No socket',
            0x41: 'Command not executable'
        }
        self.description = descriptions[self.status_code]

        super().__init__(f'Error when executing command: {self.description}')


class NoQueryResponse(TimeoutError):
    """Raised when a response cannot be obtained to a query after a number of retries"""
    
    
    
