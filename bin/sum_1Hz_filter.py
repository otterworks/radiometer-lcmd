#!/usr/bin/env python3
"""

"""

import select
import serial
import struct
import time
import lcm

from collections import deque

from radiometer_lcmtypes.raw import floats_t
from radiometer_lcmtypes.marine_sensor import radiometer_t
# downwelling_photon_spherical_irradiance mol m-2 s-1
# | downwelling_photon_flux_in_sea_water mol m-2 s-1
# | downwelling_photon_radiance_in_sea_water mol m-2 s-1 sr-1
# + bioluminescent_photon_rate_in_sea_water s-1 m-3


class SumOneHertzFilter:

    def __init__(self, width=20, verbose=0):
        self.lcm = lcm.LCM()
        self.data = deque(maxlen=width)
        self.verbose = verbose

    def heartbeat_sync(self, channel, data):
        self.data.clear()

    def handler(self, channel, data):
        """receive scaled log counts and publish estimated irradiance
        """
        rx = floats_t.decode(data)
        self.data.append(sum(rx.data))
        if len(self.data) == self.data.maxlen:
            tx = radiometer_t()
            tx.utime = rx.utime
            tx.downwelling_photon_spherical_irradiance = sum(self.data)
            if self.verbose > 0:
                print(tx.downwelling_photon_spherical_irradiance)
            tx_channel = "{0}sum1Hz".format(channel, self.data.maxlen)
            self.lcm.publish(tx_channel, tx.encode())
#        elif self.verbose > -1:
#            print("window not full: {0} < {1}".format(len(self.data),
#                self.data.maxlen))

    def filter(self, channel='RAD2d'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        sync_subscription = self.lcm.subscribe(channel[:-1] + 'h',
                self.heartbeat_sync)
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()


def main(channel='RAD2d', width=40, verbose=0):
    """Run as a daemon."""
    bf = SumOneHertzFilter(width=width, verbose=verbose)
    bf.filter(channel);


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LCM daemon to filter radiometer data")
    p.add_argument('-v', '--verbose', action='count', default=0,
                   help='display verbose output')
    p.add_argument('-V', '--version', action='version',
                   version='%(prog)s 0.0.1',
                   help='display version information and exit')
    p.add_argument('-c', '--channel', default='RAD2d',
                   help='channel to listen on')
    p.add_argument('-w', '--width', type=int, default=20,
                   help='window width in ensembles')

    a = p.parse_args()
    main(**a.__dict__)
