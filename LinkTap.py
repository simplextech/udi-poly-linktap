#!/usr/bin/env python

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import sys
import linktap

LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'LinkTap Controller'
        # self.poly.onConfig(self.process_config)
        self.username = ''
        self.apiKey = ''
        self.data = None
        self.ready = False

    def start(self):
        LOGGER.info('Started LinkTap NodeServer')
        self.removeNoticesAll()
        if self.check_params():
            self.getLinkTapDevices()
            self.discover()
            self.ready = True
            # self.poly.add_custom_config_docs("<b>And this is some custom config data</b>")

    def getLinkTapDevices(self):
        lt = linktap.LinkTap(self.username, self.apiKey)
        all_devices = lt.getAllDevices()
        self.data = all_devices

    def shortPoll(self):
        pass

    def longPoll(self):
        if self.ready:
            self.getLinkTapDevices()
            self.update()
        else:
            pass

    def update(self):
        for node in self.nodes:
            if self.nodes[node].address != self.address:
                for gw in self.data['devices']:
                    if gw['gatewayId'][0:8].lower() == self.nodes[node].address:
                        if gw['status'] == 'Connected':
                            self.nodes[node].setDriver('ST', 1)
                            #LOGGER.info('Status: Connected')
                        else:
                            self.nodes[node].setDriver('ST', 0)
                            #LOGGER.info('Status: Disconnected')
                    for tl in gw['taplinker']:
                        if tl['taplinkerId'][0:8].lower() == self.nodes[node].address:
                            if tl['status'] == 'Connected':
                                self.nodes[node].setDriver('ST', 1)
                                #LOGGER.info('Status: Connected')
                            else:
                                self.nodes[node].setDriver('ST', 0)
                                #LOGGER.info('Status: Disconnected')
                            self.nodes[node].setDriver('BATLVL', tl['batteryStatus'].strip('%'))
                            self.nodes[node].setDriver('GV0', tl['signal'].strip('%'))
                            if tl['watering'] is not None:
                                self.nodes[node].setDriver('GV1', 1)
                                for key in tl['watering']:
                                    if key == 'remaining':
                                        self.nodes[node].setDriver('GV2', tl['watering'][key])
                                    if key == 'total':
                                        self.nodes[node].setDriver('GV3', tl['watering'][key])
                            else:
                                self.nodes[node].setDriver('GV1', 0)
                                self.nodes[node].setDriver('GV2', 0)
                                self.nodes[node].setDriver('GV3', 0)

    def query(self):
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):

        all_devices = self.data

        for ctl in all_devices['devices']:
            gw_name = ctl['name']
            gw_address = ctl['gatewayId'][0:8].lower()
            self.addNode(GatewayNode(self, gw_address, gw_address, gw_name))
            for tl in ctl['taplinker']:
                tl_name = tl['taplinkerName']
                tl_address = tl['taplinkerId'][0:8].lower()
                self.addNode(TapLinkNode(self, gw_address, tl_address, tl_name))

    def delete(self):

        LOGGER.info('LinkTap Nodeserver:  Deleted')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter config={}".format(config));
        LOGGER.info("process_config: Exit");

    def check_params(self):
        default_username = "YourUserName"
        default_apiKey = "YourApiKey"

        if 'username' in self.polyConfig['customParams']:
            self.username = self.polyConfig['customParams']['username']
        else:
            self.username = default_username
            LOGGER.error('check_params: user not defined in customParams, please add it.  '
                         'Using {}'.format(self.username))

        if 'apiKey' in self.polyConfig['customParams']:
            self.apiKey = self.polyConfig['customParams']['apiKey']
        else:
            self.apiKey = default_apiKey
            LOGGER.error('check_params: apiKey not defined in customParams, please add it.  '
                         'Using {}'.format(self.apiKey))

        self.addCustomParam({'apiKey': self.apiKey, 'username': self.username})

        if self.username == default_username or self.apiKey == default_apiKey:
            self.addNotice('Please set proper user and apiKey in configuration page, and restart this nodeserver')
            return False
        else:
            return True

    def remove_notice_test(self, command):
        LOGGER.info('remove_notice_test: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNotice('test')

    def remove_notices_all(self, command):
        LOGGER.info('remove_notices_all: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self, command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    """
    Optional.
    Since the controller is the parent node in ISY, it will actual show up as a node.
    So it needs to know the drivers and what id it will use. The drivers are
    the defaults in the parent Class, so you don't need them unless you want to add to
    them. The ST and GV1 variables are for reporting status through Polyglot to ISY,
    DO NOT remove them. UOM 2 is boolean.
    The id must match the nodeDef id="controller"
    In the nodedefs.xml
    """
    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile
        #'REMOVE_NOTICES_ALL': remove_notices_all,
        #'REMOVE_NOTICE_TEST': remove_notice_test
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class GatewayNode(polyinterface.Node):
    """
    This is the class that all the Nodes will be represented by. You will add this to
    Polyglot/ISY with the controller.addNode method.

    Class Variables:
    self.primary: String address of the Controller node.
    self.parent: Easy access to the Controller Class from the node itself.
    self.address: String address of this Node 14 character limit. (ISY limitation)
    self.added: Boolean Confirmed added to ISY

    Class Methods:
    start(): This method is called once polyglot confirms the node is added to ISY.
    setDriver('ST', 1, report = True, force = False):
        This sets the driver 'ST' to 1. If report is False we do not report it to
        Polyglot/ISY. If force is True, we send a report even if the value hasn't changed.
    reportDrivers(): Forces a full update of all drivers to Polyglot/ISY.
    query(): Called when ISY sends a query request to Polyglot for this specific node
    """
    def __init__(self, controller, primary, address, name):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.

        :param controller: Reference to the Controller class
        :param primary: Controller address
        :param address: This nodes address
        :param name: This nodes name
        """
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


    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]
    """
    Optional.
    This is an array of dictionary items containing the variable names(drivers)
    values and uoms(units of measure) from ISY. This is how ISY knows what kind
    of variable to display. Check the UOM's in the WSDK for a complete list.
    UOM 2 is boolean so the ISY will display 'True/False'
    """
    id = 'gateway'
    """
    id of the node from the nodedefs.xml that is in the profile.zip. This tells
    the ISY what fields and commands this node has.
    """
    commands = {
                    'DON': setOn, 'DOF': setOff
                }


class TapLinkNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.

        :param controller: Reference to the Controller class
        :param primary: Controller address
        :param address: This nodes address
        :param name: This nodes name
        """
        super(TapLinkNode, self).__init__(controller, primary, address, name)
        self.data = controller.data
        self.primary = primary

    def start(self):
        for gw in self.data['devices']:
            for tl in gw['taplinker']:
                if tl['taplinkerId'][0:8].lower() == self.address:
                    if tl['status'] == 'Connected':
                        self.setDriver('ST', 1)
                    else:
                        self.setDriver('ST', 0)

    def setOn(self, command):
        self.setDriver('ST', 1)

    def setOff(self, command):
        self.setDriver('ST', 0)

    def query(self):
        self.reportDrivers()

    def instantOn(self, command):
        dev_suffix = '004B1200'
        cmd = command.get('cmd')
        val = command.get('value')
        taplinker = command.get('address') + dev_suffix
        gateway = self.primary + dev_suffix
        duration = int(val)

        if duration == 0:
            action = False
        else:
            action = True

        eco = False

        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activateInstantMode(gateway, taplinker, action, duration, eco)

    def intervalMode(self, command):
        dev_suffix = '004B1200'
        taplinker = command.get('address') + dev_suffix
        gateway = self.primary + dev_suffix

        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activateIntervalMode(gateway, taplinker)

    def oddEvenMode(self, command):
        dev_suffix = '004B1200'
        taplinker = command.get('address') + dev_suffix
        gateway = self.primary + dev_suffix

        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activateOddEvenMode(gateway, taplinker)

    def sevenDayMode(self, command):
        dev_suffix = '004B1200'
        taplinker = command.get('address') + dev_suffix
        gateway = self.primary + dev_suffix

        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activateSevenDayMode(gateway, taplinker)

    def monthMode(self, command):
        dev_suffix = '004B1200'
        taplinker = command.get('address') + dev_suffix
        gateway = self.primary + dev_suffix

        lt = linktap.LinkTap(self.controller.username, self.controller.apiKey)
        lt.activateMonthMode(gateway, taplinker)

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    #hint = [1,2,3,4]
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
    """
    Optional.
    This is an array of dictionary items containing the variable names(drivers)
    values and uoms(units of measure) from ISY. This is how ISY knows what kind
    of variable to display. Check the UOM's in the WSDK for a complete list.
    UOM 2 is boolean so the ISY will display 'True/False'
    """
    id = 'taplinker'
    """
    id of the node from the nodedefs.xml that is in the profile.zip. This tells
    the ISY what fields and commands this node has.
    """
    commands = {
                'GV5': instantOn, 'GV6': intervalMode, 'GV7': oddEvenMode, 'GV8': sevenDayMode, 'GV9': monthMode
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
