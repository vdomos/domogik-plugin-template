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

Plugin purpose
==============

Sample template plugin

Implements
==========


@author: domos  (domos dt vesta at gmail dt com)
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.plugin import Plugin
from domogikmq.message import MQMessage

from domogik_packages.plugin_template.lib.template import Template
from domogik_packages.plugin_template.lib.template import TemplateException

import threading
import time


class templateManager(Plugin):
    """
    """

    # -------------------------------------------------------------------------------------------------
    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='template')

        # Check if the plugin is configured. If not, this will stop the plugin and log an error
        if not self.check_configured():                     # Plugin must be configured in Domogik "Configuration Panel" otherwise plugin exit.
            return

        # Get all plugin config keys
        self.updatetime = self.get_config("updatetime")     # keys's name are declared in info.json

        # Get the devices list in plugin, if no devices are created we won't be able to use devices.
        self.devices = self.get_device_list(quit_if_no_device=True)
        self.log.debug(u"+++ devices list: %s" % format(self.devices))
        # Exemple: [{u'info_changed': u'2017-05-31 21:49:48', u'commands': {}, u'description': u'', u'reference': u'', u'xpl_stats': {}, u'xpl_commands': {}, u'client_version': u'0.1', u'client_id': u'plugin-template.hades', u'device_type_id': u'template.number', u'sensors': {u'number-sensor_template': {u'conversion': u'', u'value_min': None, u'data_type': u'DT_Number', u'reference': u'number-sensor_template', u'last_received': 1496263468, u'value_max': 43.0, u'incremental': False, u'timeout': 300, u'formula': None, u'last_value': u'43', u'id': 282, u'name': u'Number template Value'}}, u'parameters': {u'interval1': {u'key': u'interval1', u'type': u'integer', u'id': 62, u'value': u'0'}, u'interval2': {u'key': u'interval2', u'type': u'integer', u'id': 63, u'value': u'100'}}, u'id': 39, u'name': u'TNumber 1'}, {u'info_changed': u'2017-05-31 21:50:32', u'commands': {u'onoff-cmd_template': {u'return_confirmation': True, u'id': 7, u'parameters': [{u'conversion': u'', u'key': u'state', u'data_type': u'DT_Switch'}], u'name': u'OnOff Template Cmd'}}, u'description': u'', u'reference': u'', u'xpl_stats': {}, u'xpl_commands': {}, u'client_version': u'0.1', u'client_id': u'plugin-template.hades', u'device_type_id': u'template.switch', u'sensors': {u'onoff-sensor_template': {u'conversion': u'', u'value_min': None, u'data_type': u'DT_Switch', u'reference': u'onoff-sensor_template', u'last_received': 1496263301, u'value_max': 1.0, u'incremental': False, u'timeout': 0, u'formula': None, u'last_value': u'1', u'id': 283, u'name': u'OnOff template state'}}, u'parameters': {}, u'id': 40, u'name': u'TSwitch 1'}]

        # Get the sensors id per device:
        self.sensors = self.get_sensors(self.devices)
        self.log.debug(u"+++ sensors list: %s" % format(self.sensors))   # ==> sensors:   {'device id': 'sensorid_name': 'sensor id'}
        # Exemple: {40: {u'onoff-sensor_template': 283}, 39: {u'number-sensor_template': 282}}

        # Init plugin functions (declared in plugin lib)
        self.templateMng = Template(self.log, self.send_pub_data, self.get_stop(), self.updatetime )
        
        # Set plugin devices list with name and parameters
        self.setTemplateDevicesList(self.devices)

        # A thread is launched for reading sensors every time interval.
        self.log.info(u"==> Launch 'Template reading sensors' thread") 
        thr_name = "thr_readingtemplatesensors"
        self.thread_sensors = threading.Thread(None,
                                          self.templateMng.readTemplateSensorsLoop,
                                          thr_name,
                                          (),
                                          {})
        self.thread_sensors.start()
        self.register_thread(self.thread_sensors)

        # Add callback "self.reload_devices" function will be call every new/update/delete devices.
        self.log.info(u"==> Add callback for new or changed devices.")
        self.register_cb_update_devices(self.reload_devices)
        
        #self.log.info(u"==> Add devices detection test.")
        #self.add_detected_device("template.number", "Mon device 1", "ref 1", "descrip 1", 15, 20)
        #self.add_detected_device("template.switch", "Mon device 2", "ref 2", "descrip 2", "", "")
        
        self.ready()

    # -------------------------------------------------------------------------------------------------
    def setTemplateDevicesList(self, devices):
        """
            Generates a devices list with the necessary parameters;
            This list will be use in readTemplateSensorsLoop or on_mdp_request to retrieve some informations of sensors/command
        """
        self.log.info(u"==> Set plugin devices list ...")
        self.templatedevices_list = {}        
        for a_device in devices:    # For each device
            self.log.debug(u"a_device:   %s" % format(a_device))
            if a_device["device_type_id"] == "template.number":  
                interval1 = self.get_parameter(a_device, "interval1") 
                interval2 = self.get_parameter(a_device, "interval2") 
                self.templatedevices_list.update(
                    {a_device["id"] : 
                        { 'name': a_device["name"], 
                          'devicetype': a_device["device_type_id"],
                          'interval1': interval1 ,
                          'interval2': interval2
                        }
                    })
            else:
                self.templatedevices_list.update(
                    {a_device["id"] : 
                        { 'name': a_device["name"], 
                          'devicetype': a_device["device_type_id"]
                        }
                    })
            self.log.info(u"==> Device template '{0}'" . format(self.templatedevices_list[a_device["id"]]))
        self.templateMng.reloadTemplateDevices(self.templatedevices_list)
                        
 
    # -------------------------------------------------------------------------------------------------
    def on_mdp_request(self, msg):
        """ Called when a MQ req/rep message/command is received
        """
        Plugin.on_mdp_request(self, msg)
    
        if msg.get_action() == "client.cmd":                                    # If command received
            data = msg.get_data()                                               # Exemple: data='{u'state': u'1', u'command_id': 7, u'device_id': 40}'
            devicename = self.templatedevices_list[data["device_id"]]["name"]
            devicetype = self.templatedevices_list[data["device_id"]]["devicetype"]
            self.log.info(u"==> Received command '%s' for device '%s'" % (format(data),devicename))  
            if data["device_id"] not in self.templatedevices_list:
                self.log.error(u"### Device ID '%s' unknown" % device_id)
                status = False
                reason = u"Plugin template: Unknown device ID %d" % device_id   # Reply ACK with error for received command
                self.send_rep_ack(status, reason, data['command_id'], "unknown") ;                
                return
            else:    
                if devicetype == "template.switch":                                  # Device type name,  (declared in info.json)
                    status, reason = self.templateMng.execTemplateCommand(data)      # Execute command in plugin lib function
                    # Reply ACK to received command
                    self.send_rep_ack(status, reason, data['command_id'], devicename) ;
                else:
                    self.send_rep_ack(False, u"Unknow devicetype", data['command_id'], devicename) ; # There is only one command device in this plugin



    # -------------------------------------------------------------------------------------------------
    def send_rep_ack(self, status, reason, cmd_id, dev_name):
        """ Send ACQ to a command via MQ
        """
        self.log.info(u"==> Reply ACK to command id '%s' for device '%s'" % (cmd_id, dev_name))
        reply_msg = MQMessage()
        reply_msg.set_action('client.cmd.result')
        reply_msg.add_data('status', status)
        reply_msg.add_data('reason', reason)
        self.reply(reply_msg.get())


    # -------------------------------------------------------------------------------------------------
    def send_pub_data(self, device_id, sensorid_name, value):
        """ Send the sensors values over MQ
        """
        data = {}
        data[self.sensors[device_id][sensorid_name]] = value                    # data['sensor_id'] = value
        # sensorid_name = "number-sensor_template" | "onoff-sensor_template" (declared in info.json)
        try:
            self.log.info(u"==> SEND sensor value '%s' by MQ" % format(data))    # {u'sensor_id': u'value'} => {159: u'1'}
            self._pub.send_event('client.sensor', data)
        except:
            # We ignore the message if some values are not correct ...
            self.log.error(u"### Error while sending sensor value by MQ : {0}".format(data))


    # -------------------------------------------------------------------------------------------------
    def reload_devices(self, devices):
        """ Called when some devices are added/deleted/updated
        """
        self.log.info(u"==> Reload Device called")      # With n 'Global parameters', there are n calls
        self.setTemplateDevicesList(devices)
        self.devices = devices
        self.sensors = self.get_sensors(devices)


    # -------------------------------------------------------------------------------------------------
    def add_detected_device(self, devicetype, name, ref, des, interval1, interval2):
        data = {}
        data["device_type"] = devicetype
        data["name"] = name
        data["reference"] = ref
        data["description"] = des
        data["global"] = []
        if devicetype == "template.number":
            data["global"].append({"key": "interval1", "value": interval1})
            data["global"].append({"key": "interval2", "value": interval2})
        data["xpl"] = []
        data["xpl_stats"] = []
        data["xpl_commands"] = []
            
        self.device_detected(data)
        

# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    templateManager()


