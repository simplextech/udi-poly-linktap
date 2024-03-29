#!/usr/bin/env python

import sys
import linktap
import time
import logging

try:
    import polyinterface
    CLOUD = False
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True


LOGGER = polyinterface.LOGGER
logging.getLogger('urllib3').setLevel(logging.INFO)


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'LinkTap Controller'
        # self.poly.onConfig(self.process_config)
        self.username = ''
        self.apiKey = ''
        self.data = None
        self.ready = False
        self.retry_count = 1

    def start(self):
        LOGGER.info('Started LinkTap NodeServer')
        if self.check_params():
            self.discover()

    def get_link_tap_devices(self):
        lt = linktap.LinkTap(self.username, self.apiKey)
        all_devices = lt.get_all_devices()
        if all_devices == 'error':
            LOGGER.info("get_link_tap_devices: The minimum interval of calling this API is 5 minutes.")
            self.data = None
            self.ready = False
            return False
        elif all_devices is None:
            LOGGER.info("Get all devices failed")
            self.data = None
            self.ready = False
            return False
        else:
            self.data = all_devices
            self.ready = True
            return True

    def shortPoll(self):
        # Update Watering Status
        if self.ready:
            # LOGGER.info("Updating Watering Status")
            for node in self.nodes:
                if self.nodes[node].address != self.address:
                    for gw in self.data['devices']:
                        for tl in gw['taplinker']:
                            if tl['taplinkerId'][0:8].lower() == self.nodes[node].address:
                                if tl['status'] == 'Connected':
                                    link_tap = linktap.LinkTap(self.username, self.apiKey)
                                    watering_status = link_tap.get_watering_status(tl['taplinkerId'])
                                    # print(watering_status)
                                    try:
                                        if watering_status['status'] is not None:
                                            if watering_status['status']['onDuration']:
                                                self.nodes[node].setDriver('GV1', 1)
                                                self.nodes[node].setDriver('GV2', watering_status['status']['onDuration'])
                                            if watering_status['status']['total']:
                                                self.nodes[node].setDriver('GV3', watering_status['status']['total'])
                                                watering_total = int(watering_status['status']['total'])
                                                watering_duration = int(watering_status['status']['onDuration'])
                                                watering_elapsed = watering_total - watering_duration
                                                self.nodes[node].setDriver('GV4', watering_elapsed)
                                        else:
                                            self.nodes[node].setDriver('GV1', 0)
                                            self.nodes[node].setDriver('GV2', 0)
                                            self.nodes[node].setDriver('GV3', 0)
                                            self.nodes[node].setDriver('GV4', 0)
                                    except TypeError:
                                        pass
        else:
            pass

    def longPoll(self):
        if self.ready:
            if self.get_link_tap_devices():
                self.update()
            else:
                LOGGER.info("LinkTap Devices API returned None")
        else:
            pass

    def update(self):
        if self.ready:
            for node in self.nodes:
                if self.nodes[node].address != self.address:
                    for gw in self.data['devices']:
                        if gw['gatewayId'][0:8].lower() == self.nodes[node].address:
                            if gw['status'] == 'Connected':
                                self.nodes[node].setDriver('ST', 1, force=False)
                            else:
                                self.nodes[node].setDriver('ST', 0, force=False)
                        for tl in gw['taplinker']:
                            if tl['taplinkerId'][0:8].lower() == self.nodes[node].address:
                                if tl['status'] == 'Connected':
                                    self.nodes[node].setDriver('ST', 1, force=False)
                                else:
                                    self.nodes[node].setDriver('ST', 0, force=False)
                                self.nodes[node].setDriver('BATLVL', tl['batteryStatus'].strip('%'), force=False)
                                # self.nodes[node].setDriver('GV0', tl['signal'].strip('%'), force=False)
                                self.nodes[node].setDriver('GV0', tl['signal'], force=False)
                                if tl['watering'] is not None:
                                    self.nodes[node].setDriver('GV1', 1, force=False)
                                    for key in tl['watering']:
                                        if key == 'remaining':
                                            self.nodes[node].setDriver('GV2', tl['watering'][key], force=False)
                                        if key == 'total':
                                            self.nodes[node].setDriver('GV3', tl['watering'][key], force=False)
                                else:
                                    self.nodes[node].setDriver('GV1', 0, force=False)
                                    self.nodes[node].setDriver('GV2', 0, force=False)
                                    self.nodes[node].setDriver('GV3', 0, force=False)

    def query(self):
        if self.ready:
            self.check_params()
            for node in self.nodes:
                self.nodes[node].reportDrivers()

    def discover_retry(self):
        retry_count = str(self.retry_count)
        if self.retry_count <= 3000:
            LOGGER.info("discover_retry: Failed to start.  Retrying attempt: " + retry_count)
            self.retry_count += 1
            self.discover()
        else:
            LOGGER.info("discover_retry: Failed to start after 3000 retries.  Aborting")
            polyglot.stop()

    def discover(self, *args, **kwargs):
        if self.get_link_tap_devices():
            for ctl in self.data['devices']:
                gw_name = ctl['name']
                gw_address = ctl['gatewayId'][0:8].lower()
                self.addNode(GatewayNode(self, gw_address, gw_address, gw_name))
                time.sleep(2)
                for tl in ctl['taplinker']:
                    tl_name = tl['taplinkerName']
                    tl_address = tl['taplinkerId'][0:8].lower()
                    self.addNode(TapLinkNode(self, gw_address, tl_address, tl_name))
                    time.sleep(2)
            self.ready = True
            self.update()
        else:
            LOGGER.info("Failed to get devices.  Will retry in 5 minutes")
            self.ready = False
            time.sleep(300)
            self.discover_retry()

    def delete(self):
        LOGGER.info('LinkTap Nodeserver:  Deleted')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter config={}".format(config))
        LOGGER.info("process_config: Exit")

    def check_params(self):
        default_username = "YourUserName"
        default_api_key = "YourApiKey"

        if 'username' in self.polyConfig['customParams']:
            self.username = self.polyConfig['customParams']['username']
        else:
            self.username = default_username
            LOGGER.error('check_params: user not defined in customParams, please add it.  '
                         'Using {}'.format(self.username))

        if 'apiKey' in self.polyConfig['customParams']:
            self.apiKey = self.polyConfig['customParams']['apiKey']
        else:
            self.apiKey = default_api_key
            LOGGER.error('check_params: apiKey not defined in customParams, please add it.  '
                         'Using {}'.format(self.apiKey))

        self.addCustomParam({'username': self.username, 'apiKey': self.apiKey})
        time.sleep(2)

        if self.username == default_username or self.apiKey == default_api_key:
            self.addNotice({'params_notice': 'Please set proper user and apiKey in '
                            'configuration page, and restart this nodeserver'})
            return False
        else:
            self.remove_notices_all()
            return True

    def remove_notice_test(self, command):
        LOGGER.info('remove_notice_test: notices={}'.format(self.poly.config['notices']))
        # Remove named notices
        self.removeNotice('test')

    def remove_notices_all(self):
        LOGGER.info('remove_notices_all: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self, command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class GatewayNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(GatewayNode, self).__init__(controller, primary, address, name)
        self.data = controller.data

    def start(self):
        for gw in self.data['devices']:
            if gw['gatewayId'][0:8].lower() == self.address:
                if gw['status'] == 'Connected':
                    self.setDriver('ST', 1)
                else:
                    self.setDriver('ST', 0)

    def setOn(self, command):
        self.setDriver('ST', 1)

    def setOff(self, command):
        self.setDriver('ST', 0)

    def query(self):
        self.reportDrivers()

    def update(self):
        for gw in self.data['devices']:
            if gw['gatewayId'][0:8].lower() == self.address:
                if gw['status'] == 'Connected':
                    self.setDriver('ST', 1)
                else:
                    self.setDriver('ST', 0)


    # "Hints See: https://github.com/UniversalDevicesInc/hints"
    # hint = [1,2,3,4]
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]
    id = 'gateway'

    commands = {
                    'DON': setOn, 'DOF': setOff
                }


class TapLinkNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(TapLinkNode, self).__init__(controller, primary, address, name)
        self.data = controller.data
        self.primary = primary
        self.dev_suffix = '004B1200'

    def start(self):
        for gw in self.data['devices']:
            for tl in gw['taplinker']:
                if tl['taplinkerId'][0:8].lower() == self.address:
                    if tl['status'] == 'Connected':
                        self.setDriver('ST', 1, force=True)
                    else:
                        self.setDriver('ST', 0, force=True)
                    self.setDriver('BATLVL', tl['batteryStatus'].strip('%'), force=True)
                    # self.setDriver('GV0', tl['signal'].strip('%'), force=True)
                    self.setDriver('GV0', tl['signal'], force=True)
                    if tl['watering'] is not None:
                        self.setDriver('GV1', 1, force=True)
                        for key in tl['watering']:
                            if key == 'remaining':
                                self.setDriver('GV2', tl['watering'][key], force=True)
                            if key == 'total':
                                self.setDriver('GV3', tl['watering'][key], force=True)
                    else:
                        self.setDriver('GV1', 0, force=True)
                        self.setDriver('GV2', 0, force=True)
                        self.setDriver('GV3', 0, force=True)

    def setOn(self, command):
        self.setDriver('ST', 1)

    def setOff(self, command):
        self.setDriver('ST', 0)

    def query(self):
        self.reportDrivers()

    def instantOn(self, command):
        val = command.get('value')
        taplinker = command.get('address') + self.dev_suffix
        gateway = self.primary + self.dev_suffix
        duration = int(val)

        # if duration == 0:
        #     action = False
        # else:
        #     action = True
        action = True
        eco = False

        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activate_instant_mode(gateway, taplinker, action, duration, eco)
        self.setDriver('GV1', 1)
        self.setDriver('GV2', duration)
        self.setDriver('GV3', duration)

    def instantOff(self, command):
        taplinker = command.get('address') + self.dev_suffix
        gateway = self.primary + self.dev_suffix
        duration = 0
        action = False
        eco = False

        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activate_instant_mode(gateway, taplinker, action, duration, eco)
        self.setDriver('GV1', 0)
        self.setDriver('GV2', duration)
        self.setDriver('GV3', duration)


    def intervalMode(self, command):
        taplinker = command.get('address') + self.dev_suffix
        gateway = self.primary + self.dev_suffix
        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activate_interval_mode(gateway, taplinker)

    def oddEvenMode(self, command):
        taplinker = command.get('address') + self.dev_suffix
        gateway = self.primary + self.dev_suffix
        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activate_odd_even_mode(gateway, taplinker)

    def sevenDayMode(self, command):
        taplinker = command.get('address') + self.dev_suffix
        gateway = self.primary + self.dev_suffix
        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activate_seven_day_mode(gateway, taplinker)

    def monthMode(self, command):
        taplinker = command.get('address') + self.dev_suffix
        gateway = self.primary + self.dev_suffix
        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activate_month_mode(gateway, taplinker)

    # "Hints See: https://github.com/UniversalDevicesInc/hints"
    # hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'BATLVL', 'value': 0, 'uom': 51},
        {'driver': 'GV0', 'value': 0, 'uom': 51},  # Signal
        {'driver': 'GV1', 'value': 0, 'uom': 2},  # Watering
        {'driver': 'GV2', 'value': 0, 'uom': 44},  # Remaining
        {'driver': 'GV3', 'value': 0, 'uom': 44},  # Total
        {'driver': 'GV4', 'value': 0, 'uom': 44},  # Elapsed
        {'driver': 'GV5', 'value': 0, 'uom': 44},  # Instant On Minutes
    ]

    id = 'taplinker'
    commands = {
                'GV5': instantOn, 'GV10': instantOff, 'GV6': intervalMode, 'GV7': oddEvenMode,
                'GV8': sevenDayMode, 'GV9': monthMode
                }


if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('Template')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
