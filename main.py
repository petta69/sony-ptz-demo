#!/bin/python3

import sys
import os
import time
import timeit
import ipaddress
import socket

from enum import Enum
from fastapi import FastAPI, Request, Form, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

## Get settings and store in dict
from lib.settings import ReadConfig, ModelConfig, SaveConfig
config = ReadConfig()

## Configure logger object
from logger import Logger
logger = Logger(name=__name__, level=config.verbose, file_path="/tmp/sony-ptz-demo.txt").get_logger()

from lib.visca_discovery import VISCA_DEVICES
app = FastAPI(title="PTZ Camera Config")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

templates = Jinja2Templates(directory="templates")


#net4 = ipaddress.ip_network(config.network)
net4 = ipaddress.IPv4Network(config.network)
first_host = config.ptz_start_ip

 
class ModelPTZCam(str, Enum):
    '''
    Valid functions for the PTZ Camera class
    '''
    PTZCamENQ = "PTZCamENQ"
    PTZCamSetIP = "PTZCamSetIP"

class ModelSystem(str, Enum):
    '''
    Valid functions for the system class
    '''
    Restart = "Restart"


def find_visca_devices():
    config = ReadConfig()
    ## Visca discovery
    my_visca = VISCA_DEVICES(ip="255.255.255.255", port=config.visca_port, verbose=5)
    visca_list = my_visca.get_visca_devices()
    my_visca.close_connection()

    VISCA_LIST = []
    MAC_LIST = []
    
    if isinstance(visca_list, list):
        for visca in visca_list:
            if "IPADR" in visca and "MAC" in visca and "MODEL" in visca:
                if visca['MAC'] in MAC_LIST:
                    logger.debug(f"Duplicate device found with MAC: {visca['MAC']}. Skipping this entry.")
                    continue
                elif visca['MODEL'] == "IPCARD":
                    logger.debug(f"MAC: {visca['MAC']} IP: {visca['IPADR']}")
                    VISCA_LIST.append(visca)
                    MAC_LIST.append(visca['MAC'])
            else:
                logger.debug(f"The item did not contain the expected keys: {visca}")
    else:
        logger.debug("No VISCA devices found. Aborting!")
        sys.exit(1)
        
    ## Sort list by IP
    VISCA_LIST.sort(key=lambda x: ipaddress.IPv4Address(x['IPADR']))
    return VISCA_LIST


##
## API calls
##

## PTCam API functions
@app.get("/api/ptzcam/{function}")
async def ptzcam_api_function(function: ModelPTZCam):
    result = []
    try:
        config = ReadConfig()
        my_visca_devices = VISCA_DEVICES(ip="255.255.255.255", port=config.visca_port, verbose=5)
    except:
        return {"ERROR": "Could not connect to host"}
    if function is ModelPTZCam.PTZCamENQ:
        response = find_visca_devices()
        result.append(response)
    elif function is ModelPTZCam.PTZCamSetIP:
        visca_devices = find_visca_devices()
        device_ip = config.ptz_start_ip
        
        ## First we need to check if we have device with WRITE='off' and are already in correct network
        busy_IP = []
        for device in visca_devices:
            if "MAC" in device and "IPADR" in device:
                logger.debug(f"Device with MAC: {device['MAC']}. Checking if IP: {device['IPADR']} is in the correct network.")
                if ipaddress.IPv4Address(device['IPADR']) in net4 and device['WRITE'] != "on":
                    logger.debug(f"Device with MAC: {device['MAC']} is already in the correct network. Skipping IP assignment.")
                    busy_IP.append(device['IPADR'])

        
        for device in visca_devices:
            ## We only want to deal with Cameras and when WRITE is "on"
            if "MAC" in device and "IPADR" in device and device['MODEL'] == "IPCARD" and device['WRITE'] == "on":

                while True:
                    if str(net4[device_ip]) in busy_IP:
                        logger.debug(f"IP: {net4[device_ip]} is already in use by another device. Skipping this IP.")
                        device_ip = device_ip + 1
                        if device_ip >= 254:
                            logger.error("ERROR: Not enough IP addresses available in the specified range.")
                            break
                    else:
                        break
                logger.debug(f"Setting IP for device with MAC: {device['MAC']} and current IP: {device['IPADR']}")
                result.append(my_visca_devices.set_visca_device_ip(device_mac=device['MAC'], device_ip=f"{net4[device_ip]}", device_mask=net4.netmask, device_gateway=net4[1], device_name=device['NAME'])) 
                device_ip = device_ip + 1
                if device_ip >= 254:
                    logger.error("ERROR: Not enough IP addresses available in the specified range.")
                    break

    ## Wash list to return
    for result_list in result:
        for item in result_list:
            if not item:
                result_list.remove(item)
            

    return result




## TemplateResponse
@app.get("/", response_class=HTMLResponse)
async def index_visca(request: Request, function: ModelPTZCam | None=None):
    ## If we get a function we need to execute that action. Result is used to print status.
    config = ReadConfig()

    context = {}
    if function:
        result = await ptzcam_api_function(function)
        ## Create context to pass to bootstrap
        context["status"] = result

    ## Query for VISCA devices
    try:
        visca_devices = find_visca_devices()
        context["visca_devices"] = visca_devices
    except Exception as e:
        context["error"] = f"Error finding VISCA devices: {e}"

    try:
        context["config"] = config
    except Exception as e:
        context["error"] = f"Error getting host IP address: {e}"

    return templates.TemplateResponse(
        request=request, name="index.html", context=context
    )


## Help SRG
@app.get("/help_srg", response_class=HTMLResponse)
async def help_srg(request: Request):
    return templates.TemplateResponse(
        request=request, name="help_srg.html", context={}
    )


## Help BRC
@app.get("/help_brc", response_class=HTMLResponse)
async def help_srg(request: Request):
    return templates.TemplateResponse(
        request=request, name="help_brc.html", context={}
    )


## Help Companion
@app.get("/help_companion", response_class=HTMLResponse)
async def help_companion(request: Request):
    return templates.TemplateResponse(
        request=request, name="help_companion.html", context={}
    )
      

if(__name__) == '__main__':
        import uvicorn
        uvicorn.run(
        "main:app",
        host    = "0.0.0.0",
        port    = 8080, 
        reload  = True
    )