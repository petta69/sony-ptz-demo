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

from lib.srg_visca import VISCA_DEVICES
app = FastAPI(title="PTZ Camera Config")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

templates = Jinja2Templates(directory="templates")


flood_oldfunction = "none"
flood_oldtime = timeit.default_timer()
clients = []

     


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
@app.get("/api/ptzcam/{function}")
async def ptzcam_api_function(function: ModelPTZCam):
    result = []
    if check_flooding(function.value):
        return {'Error': 'Flooding'}
    try:
        config = ReadConfig()
        visca_devices = VISCA_DEVICES(ip="255.255.255.255", port=config.visca_port, verbose=5)
    except:
        return {"ERROR": "Could not connect to host"}
    if function is ModelPTZCam.PTZCamENQ:
        result.append(visca_devices.get_visca_devices())
    elif function is ModelPTZCam.PTZCamSetIP:
        result.append(visca_devices.set_visca_device_ip(device_mac="00:00:00:00:00:00", device_ip="192.168.111.10"))
    return result




## TemplateResponse
@app.get("/", response_class=HTMLResponse)
async def bravia(request: Request, function: ModelPTZCam | None=None):
    ## If we get a function we need to execute that action. Result is used to print status.
    config = ReadConfig()
    context = {}
    if function:
        result = await ptzcam_api_function(function)
        ## Create context to pass to bootstrap
        context["status"] = result

    return templates.TemplateResponse(
        request=request, name="bravia.html", context=context
    )

@app.get("/control", response_class=HTMLResponse)
async def bravia_control(request: Request, function: ModelPTZCam | None=None):
    ## If we get a function we need to execute that action. Result is used to print status.
    config = ReadConfig()
    context = {}
    if function:
        result = await ptzcam_api_function(function)
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