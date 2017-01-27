#!/usr/bin/env python
# zwave_power_meter_socket.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
ModuleName = "aeotec_heavy_switch"
INTERVAL     = 60      # How often to request sensor values

import sys
import time
import os
from cbcommslib import CbAdaptor
from cbconfig import *
from twisted.internet import threads
from twisted.internet import reactor

class Adaptor(CbAdaptor):
    def __init__(self, argv):
        self.status =           "ok"
        self.state =            "stopped"
        self.connected =        False
        self.switchState =      "unknown"
        self.apps =             {"energy": [],
                                 "power": [],
                                 "voltage": [],
                                 "current": [],
                                 "power_factor": [],
                                 "binary_sensor": [],
                                 "temperature": [],
                                 "switch": [],
                                 "connected": []}
        # super's __init__ must be called:
        #super(Adaptor, self).__init__(argv)
        CbAdaptor.__init__(self, argv)
 
    def setState(self, action):
        # error is only ever set from the running state, so set back to running if error is cleared
        if action == "error":
            self.state == "error"
        elif action == "clear_error":
            self.state = "running"
        msg = {"id": self.id,
               "status": "state",
               "state": self.state}
        self.sendManagerMessage(msg)

    def sendCharacteristic(self, characteristic, data, timeStamp):
        msg = {"id": self.id,
               "content": "characteristic",
               "characteristic": characteristic,
               "data": data,
               "timeStamp": timeStamp}
        for a in self.apps[characteristic]:
            reactor.callFromThread(self.sendMessage, msg, a)

    def onStop(self):
        # Mainly caters for situation where adaptor is told to stop while it is starting
        pass

    def pollSensors(self):
        cmd = {"id": self.id,
               "request": "post",
               "address": self.addr,
               "instance": "0",
               "commandClass": "50",
               "action": "Get",
               "value": ""
              }
        self.sendZwaveMessage(cmd)
        cmd = {"id": self.id,
               "request": "post",
               "address": self.addr,
               "instance": "0",
               "commandClass": "49",
               "action": "Get",
               "value": ""
              }
        self.sendZwaveMessage(cmd)
        reactor.callLater(INTERVAL, self.pollSensors)

    def checkConnected(self):
        if self.updateTime == self.lastUpdateTime:
            self.connected = False
        else:
            self.connected = True
        self.sendCharacteristic("connected", self.connected, time.time())
        self.lastUpdateTime = self.updateTime
        reactor.callLater(INTERVAL + 10, self.checkConnected)

    def onZwaveMessage(self, message):
        #self.cbLog("debug", "onZwaveMessage, message: " + str(message))
        if message["content"] == "init":
            self.updateTime = 0
            self.lastUpdateTime = time.time()
            # Energy - KWh
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "50",
                   "value": "0"
                  }
            self.sendZwaveMessage(cmd)
            # Power - W
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "50",
                   "value": "2"
                  }
            self.sendZwaveMessage(cmd)
            # Voltage
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "50",
                   "value": "4"
                  }
            self.sendZwaveMessage(cmd)
            # Current - A
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "50",
                   "value": "5"
                  }
            self.sendZwaveMessage(cmd)
            # Power Factor
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "50",
                   "value": "6"
                  }
            self.sendZwaveMessage(cmd)
            # Temperature
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "49",
                   "value": "1"
                  }
            self.sendZwaveMessage(cmd)
            # Switch state
            cmd = {"id": self.id,
                   "request": "get",
                   "address": self.addr,
                   "instance": "0",
                   "commandClass": "37",
                   "value": "level"
                  }
            self.sendZwaveMessage(cmd)
            reactor.callLater(30, self.pollSensors)
            reactor.callLater(INTERVAL, self.checkConnected)
        elif message["content"] == "data":
            try:
                if message["commandClass"] == "50":
                    if message["value"] == "0":
                        energy = message["data"]["val"]["value"] 
                        self.sendCharacteristic("energy", energy, time.time())
                    elif message["value"] == "2":
                        power = message["data"]["val"]["value"] 
                        self.sendCharacteristic("power", power, time.time())
                    elif message["value"] == "4":
                        voltage = message["data"]["val"]["value"] 
                        self.sendCharacteristic("voltage", voltage, time.time())
                    elif message["value"] == "5":
                        current = message["data"]["val"]["value"] 
                        self.sendCharacteristic("current", current, time.time())
                    elif message["value"] == "6":
                        power_factor = message["data"]["val"]["value"] 
                        self.sendCharacteristic("power_factor", power_factor, time.time())
                elif message["commandClass"] == "49":
                    if message["value"] == "1":
                        temperature = message["data"]["val"]["value"] 
                        #self.cbLog("debug", "onZwaveMessage, temperature: " + str(temperature))
                        self.sendCharacteristic("temperature", temperature, time.time())
                elif message["commandClass"] == "37":
                    if message["value"] == "level":
                        if message["data"]["value"]:
                            b = "on"
                        else:
                            b = "off"
                        self.switchState = b
                        self.sendCharacteristic("binary_sensor", b, time.time())
                self.updateTime = message["data"]["updateTime"]
            except Exception as ex:
                self.cbLog("warning", "onZwaveMessage, unexpected message: " + str(message))
                self.cbLog("warning", "Exception: " + str(type(ex)) + str(ex.args))

    def onOff(self, s):
        if s == "on":
            return "255"
        else:
            return "0"

    def switch(self, onOrOff):
        cmd = {"id": self.id,
               "request": "post",
               "address": self.addr,
               "instance": "0",
               "commandClass": "0x25",
               "action": "Set",
               "value": self.onOff(onOrOff)
              }
        self.sendZwaveMessage(cmd)

    def onAppInit(self, message):
        self.cbLog("debug", "onAppInit, message: " + str(message))
        resp = {"name": self.name,
                "id": self.id,
                "status": "ok",
                "service": [{"characteristic": "energy", "interval": INTERVAL, "type": "switch"},
                            {"characteristic": "power", "interval": INTERVAL, "type": "switch"},
                            {"characteristic": "voltage", "interval": INTERVAL, "type": "switch"},
                            {"characteristic": "current", "interval": INTERVAL, "type": "switch"},
                            {"characteristic": "power_factor", "interval": INTERVAL, "type": "switch"},
                            {"characteristic": "connected", "interval": INTERVAL, "type": "switch"},
                            {"characteristic": "temperature", "interval": INTERVAL, "type": "switch"},
                            {"characteristic": "binary_sensor", "interval": 0, "type": "switch"},
                            {"characteristic": "switch", "interval": 0}],
                "content": "service"}
        self.sendMessage(resp, message["id"])
        self.setState("running")

    def onAppRequest(self, message):
        # Switch off anything that already exists for this app
        for a in self.apps:
            if message["id"] in self.apps[a]:
                self.apps[a].remove(message["id"])
        # Now update details based on the message
        for f in message["service"]:
            if message["id"] not in self.apps[f["characteristic"]]:
                self.apps[f["characteristic"]].append(message["id"])
        self.cbLog("debug", "apps: " + str(self.apps))

    def onAppCommand(self, message):
        if "data" not in message:
            self.cbLog("warning", "app message without data: " + str(message))
        else:
            self.cbLog("warning", "This is a sensor. Message not understood: " +  str(message))
    def onAppCommand(self, message):
        self.cbLog("debug", "onAppCommand, req: " +  str(message))
        if "data" not in message:
            self.cbLog("warning", "app message without data: " + str(message))
        elif message["data"] != "on" and message["data"] != "off":
            self.cbLog("warning", "switch state must be on or off: " +  str(message))
        else:
            if message["data"] != self.switchState:
                self.switch(message["data"])

    def onConfigureMessage(self, config):
        """Config is based on what apps are to be connected.
            May be called again if there is a new configuration, which
            could be because a new app has been added.
        """
        self.setState("starting")

if __name__ == '__main__':
    Adaptor(sys.argv)
