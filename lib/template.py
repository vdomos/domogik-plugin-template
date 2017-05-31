#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

@author: domos  (domos p vesta at gmail p com)
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
import subprocess
import time
import random


class TemplateException(Exception):
    """
    Template exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.sensorvalue = value

    def __str__(self):
        return repr(self.value)


class Template:
    """
    """

    # -------------------------------------------------------------------------------------------------
    def __init__(self, log, send, stop, updatetime):
        """ Init Template object
            @param log : log instance
            @param send : callback to send values to domogik
            @param stop : Event of the plugin to handle plugin stop
            @param updatetime : Time in second beetween two sensor reading
        """
        self.log = log
        self.send = send
        self.stopplugin = stop
        self.updatetime = updatetime



    # -------------------------------------------------------------------------------------------------
    def reloadTemplateDevices(self, devices):
        """ Called by the bin part when starting or devices added/deleted/updated
        """
        self.templatedevices = devices


    # -------------------------------------------------------------------------------------------------
    def readTemplateSensorsLoop(self):
        """ Execute "template" sensors reading every interval secondes.
        """
        self.log.info(u"==> Thread for 'Template reading sensors' started")
        templateinfo_nextread = {}
        while not self.stopplugin.isSet():
            for deviceid in self.templatedevices:
                devicetype = self.templatedevices[deviceid]["devicetype"]
                if devicetype == "template.number": 
                    name = self.templatedevices[deviceid]["name"]
                    interval1 = self.templatedevices[deviceid]["interval1"]
                    interval2 = self.templatedevices[deviceid]["interval2"]
                    
                    # Read sensor (in this template plugin, it's only un random generate numer)
                    value = random.randint(interval1, interval2)
                    
                    self.log.info("==> UPDATE Sensor for device '%s' with value '%s' " % (name, value))
                    self.send(deviceid, "number-sensor_template", value)    # Update sensor value in Domogik, "number-sensor_template" is the sensorid_name in info.json
                    self.log.info(u"==> WAIT {0} seconds before the next sensor reading for device '{1}' ".format(self.updatetime, name))
                    self.stopplugin.wait(self.updatetime)                   # Sleep "self.updatetime" seconds or exit if plugin is stopped.
        self.log.info(u"==> Thread for 'Template reading sensors' stopped")
   

    # -------------------------------------------------------------------------------------------------
    def execTemplateCommand(self, data):
        """
            Exec received Domogik command
            @param data: {u'key_name': key_value, u'command_id': commadn_id, u'device_id': device_id}
        """
        statestr = { '0' : 'On',  '1' : 'Off'}  # Only to have a more readable log.
        
        # In this template plugin, it's only a update of sensor associated  with the command
        self.send(data["device_id"], "onoff-sensor_template", data['state'])        # 'state' is the key paremeter of the command declared in info.json
        
        self.log.debug(u"==> Command '%s' is executed with value: '%s'" % (self.templatedevices[data["device_id"]]["name"], statestr[data["state"]]))
        return True, None
            
