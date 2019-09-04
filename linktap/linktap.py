#!/usr/bin/env python3

import sys
import requests


class LinkTap:
    def __init__(self, username, apiKey):
        self.base_url = 'https://www.link-tap.com/api/'
        self.username = username
        self.apiKey = apiKey

    def activateInstantMode(self, gatewayId, taplinkerId, action, duration, eco):
        url = self.base_url + 'activateInstantMode'

        if action:
            action = "true"
        else:
            action = "false"

        if eco:
            eco = "true"
        else:
            eco = "false"

        payload = {'username': self.username,
                   'apiKey': self.apiKey,
                   'gatewayId': gatewayId,
                   'taplinkerId': taplinkerId,
                   'action': action,
                   'duration': duration,
                   'eco': eco}

        r = requests.post(url, data=payload)
        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            # print(r.content)
            r.raise_for_status()

    def activateIntervalMode(self, gatewayId, taplinkerId):
        url = self.base_url + 'activateIntervalMode'

        payload = {'username': self.username,
                   'apiKey': self.apiKey,
                   'gatewayId': gatewayId,
                   'taplinkerId': taplinkerId
                   }

        r = requests.post(url, data=payload)
        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            # print(r.content)
            r.raise_for_status()

    def activateOddEvenMode(self, gatewayId, taplinkerId):
        url = self.base_url + 'activateOddEvenMode'

        payload = {'username': self.username,
                   'apiKey': self.apiKey,
                   'gatewayId': gatewayId,
                   'taplinkerId': taplinkerId
                   }

        r = requests.post(url, data=payload)
        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            # print(r.content)
            r.raise_for_status()

    def activateSevenDayMode(self, gatewayId, taplinkerId):
        url = self.base_url + 'activateSevenDayMode'

        payload = {'username': self.username,
                   'apiKey': self.apiKey,
                   'gatewayId': gatewayId,
                   'taplinkerId': taplinkerId
                   }

        r = requests.post(url, data=payload)
        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            # print(r.content)
            r.raise_for_status()

    def activateMonthMode(self, gatewayId, taplinkerId):
        url = self.base_url + 'activateMonthMode'

        payload = {'username': self.username,
                   'apiKey': self.apiKey,
                   'gatewayId': gatewayId,
                   'taplinkerId': taplinkerId
                   }

        r = requests.post(url, data=payload)
        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            # print(r.status_code)
            r.raise_for_status()

    def getAllDevices(self):
        url = self.base_url + 'getAllDevices'
        payload = {'username': self.username, 'apiKey': self.apiKey}
        r = requests.post(url, data=payload)

        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            # print(r.status_code)
            r.raise_for_status()


if __name__ == "__main__":
    try:
        import json

        with open('test_data.json') as json_file:
            all_devices = json.load(json_file)

        #lt = LinkTap()
        #all_devices = lt.getAllDevices()
        for ctl in all_devices['devices']:
            print('Name: ' + ctl['name'])
            print('Gateway ID: ' + ctl['gatewayId'])
            print('ISY GW ID: ' + ctl['gatewayId'][0:8].lower())
            for tl in ctl['taplinker']:
                print('TL Name: ' + tl['taplinkerName'])
                print('TL ID: ' + tl['taplinkerId'][0:8].lower())

        for gw in all_devices['devices']:
            for tl in gw['taplinker']:
                if tl['taplinkerId'][0:8].lower():
                    if tl['status'] == 'Connected':
                        print("setting driver ON")
                    else:
                        print("setting driver OFF")
                    if tl['watering'] is not None:
                        for i in tl['watering']:
                            print(i)
                            print(tl['watering'][i])
                        # print('Watering Remaining')


        # for ctl in all_devices['devices']:
        #     for tl in ctl['taplinker']:
        #         print('TL Name: ' + tl['taplinkerName'])
        #         print('TL ID: ' + tl['taplinkerId'][0:8].lower())

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)