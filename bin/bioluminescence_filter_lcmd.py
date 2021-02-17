#!/usr/bin/env python3
"""Bioluminescence filter for Future Ocean Lab radiometer data

    Filters out spikes from bioluminescent events to give the ambient irradiance.
"""

import select
import serial
import struct
import time
import lcm

from collections import deque
from numpy import median

from mesobot_lcmtypes.raw import bytes_t
from mesobot_lcmtypes.marine_sensor import radiometer_t
# downwelling_photon_spherical_irradiance mol m-2 s-1
# | downwelling_photon_flux_in_sea_water mol m-2 s-1
# | downwelling_photon_radiance_in_sea_water mol m-2 s-1 sr-1
# + bioluminescent_photon_rate_in_sea_water s-1 m-3


class BioluminescenceFilter:

    def __init__(self, width=2000, verbose=0):
        self.lcm = lcm.LCM()
        self.data = deque(maxlen=width)
        self.verbose = verbose

    def estimate_ambient(self,):
        """Estimate the ambient *downwelling_photon_spherical_irradiance*

        This does the heavly lifting.
        """
        return median(self.data) # TODO: implement Dana's existing filter

    def handler(self, channel, data):
        """receive scaled log counts and publish estimated irradiance
        """
        rx = bytes_t.decode(data)
        fmt = '<8x{0}H'.format(int((rx.length-8)/2)) # nominal 2HL50H, but we just want 50H
        self.data.extend(struct.unpack(fmt, rx.data))
        if len(self.data) == self.data.maxlen:
            tx = radiometer_t()
            tx.utime = rx.utime
            tx.downwelling_photon_spherical_irradiance = self.estimate_ambient()
            print(tx.downwelling_photon_spherical_irradiance)
            self.lcm.publish("{0}f".format(channel), tx.encode())
        else:
            print("window not full: {0} < {1}".format(len(self.data),
                self.data.maxlen))

    def filter(self, channel='RADo'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()


def main(channel='RADo', width=2000, verbose=0):
    """Run as a daemon."""
    bf = BioluminescenceFilter(width=width, verbose=verbose)
    bf.filter(channel);


if __name__ == "__main__":
    import argparse
    P = argparse.ArgumentParser(description="LCM daemon to filter radiometer data")
    P.add_argument('-v', '--verbose', action='count', default=0,
                   help='display verbose output')
    P.add_argument('-V', '--version', action='version',
                   version='%(prog)s 0.0.1',
                   help='display version information and exit')
    P.add_argument('-c', '--channel', default='RADo',
                   help='channel to listen on')
    A = P.parse_args()
    main(**A.__dict__)
