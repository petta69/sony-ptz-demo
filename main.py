#!/bin/python3

import sys
import os
import time
import timeit

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
logger = Logger(name=__name__, level=config.verbose, file_path="/tmp/rsony_bravia_controller.txt").get_logger()

from bravia_restAPI import BRAVIA_RESTAPI
from sony_bluray import bluray_player
#from lib.system import reboot_rpi


app = FastAPI(title="BRAVIA Control")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/icons", StaticFiles(directory="icons"), name="icons")

templates = Jinja2Templates(directory="templates")


flood_oldfunction = "none"
flood_oldtime = timeit.default_timer()
clients = []

class ModelBRAVIA(str, Enum):
     '''
     Valid functions for the BRAVIA class
     '''
     SetBrightness10 = "SetBrightness10"
     SetBrightness25 = "SetBrightness25"
     SetBrightness49 = "SetBrightness49"
     GetBrightness = "GetBrightness"
     SetPowerOn = "SetPowerOn"
     SetPowerOff = "SetPowerOff"
     GetPowerStatus = "GetPowerStatus"
     


class ModelBluRay(str, Enum):
    '''
    Valid functions for the BluRay class
    '''
    BluRay_SetPowerOn = "BluRay_SetPowerOn"
    BluRay_SetPowerOff = "BluRay_SetPowerOff"
    BluRay_Play = "BluRay_Play"
    BluRay_Pause = "BluRay_Pause"
    BluRay_Stop = "BluRay_Stop"

class ModelSystem(str, Enum):
    '''
    Valid functions for the system class
    '''
    Restart = "Restart"

def check_flooding(flood_function, flood_timeout=5):
    global flood_oldfunction
    global flood_oldtime
    now = timeit.default_timer()
    if flood_function == flood_oldfunction:
        if now - flood_oldtime < flood_timeout:
            flood_oldtime = now
            return True
        else:
            flood_oldtime = now
            return False
    else:
        flood_oldfunction = flood_function
        flood_oldtime = now
        return False
    

##
## API calls
##

## BRAVIA
@app.get("/api/bravia/{function}")
async def bravia_api_function(function: ModelBRAVIA):
    result = []
    if check_flooding(function.value):
        return {'Error': 'Flooding'}
    try:
        config = ReadConfig()
        bravia1 = BRAVIA_RESTAPI(host_ip=config.bravia_host_01, psk=config.bravia_psk_01)
        bravia2 = BRAVIA_RESTAPI(host_ip=config.bravia_host_02, psk=config.bravia_psk_02)
    except:
        return {"ERROR": "Could not connect to host"}
    if function is ModelBRAVIA.SetBrightness10:
        result.append(bravia1.set_brightness(23))
        result.append(bravia2.set_brightness(25))
    elif function is ModelBRAVIA.SetBrightness25:
        result.append(bravia1.set_brightness(45))
        result.append(bravia2.set_brightness(49))
    elif function is ModelBRAVIA.SetBrightness49:
        result.append(bravia1.set_brightness(49))
        result.append(bravia2.set_brightness(49))
    elif function is ModelBRAVIA.SetPowerOn:
        result.append(bravia1.set_power("on"))
        result.append(bravia2.set_power("on"))
    elif function is ModelBRAVIA.SetPowerOff:
        result.append(bravia1.set_power("off"))
        result.append(bravia2.set_power("off"))
    elif function is ModelBRAVIA.GetBrightness:
        result.append(bravia1.get_brightness())
        result.append(bravia2.get_brightness())
    elif function is ModelBRAVIA.GetPowerStatus:
        result.append(bravia1.get_power_status())
        result.append(bravia2.get_power_status())
    return result

## BluRay
@app.get("/api/bluray/{function}")
async def bluray_api_function(function: ModelBluRay):
    result = []
    if check_flooding(function.value):
        return {'Error': 'Flooding'}
    try:
        config = ReadConfig()
        bluray1 = bluray_player(host_ip=config.bluray_host, port=config.bluray_port)
    except:
        return {"ERROR": "Could not connect to host"}
    if function is ModelBluRay.BluRay_Play:
        result.append(bluray1.play())
    elif function is ModelBluRay.BluRay_Pause:
        result.append(bluray1.pause())
    return result



## TemplateResponse
@app.get("/", response_class=HTMLResponse)
async def bravia(request: Request, function: ModelBRAVIA | None=None):
    ## If we get a function we need to execute that action. Result is used to print status.
    config = ReadConfig()
    context = {}
    if function:
        result = await bravia_api_function(function)
        ## Create context to pass to bootstrap
        context["status"] = result

    return templates.TemplateResponse(
        request=request, name="bravia.html", context=context
    )

@app.get("/control", response_class=HTMLResponse)
async def bravia_control(request: Request, function: ModelBRAVIA | None=None):
    ## If we get a function we need to execute that action. Result is used to print status.
    config = ReadConfig()
    context = {}
    if function:
        result = await bravia_api_function(function)
        ## Create context to pass to bootstrap
        context["status"] = result

    return templates.TemplateResponse(
        request=request, name="bravia_control.html", context=context
    )


## WebSocket connection
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        clients.remove(websocket)
        
async def notify_clients(status_text):
    logger.debug(f"Sending updated status: {status_text}")
    for client in clients:
        await client.send_text(str(status_text))
        time.sleep(2)
        

if(__name__) == '__main__':
        import uvicorn
        uvicorn.run(
        "main:app",
        host    = "0.0.0.0",
        port    = 8080, 
        reload  = True
    )