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
from numpy import mean

from radiometer_lcmtypes.raw import floats_t
from radiometer_lcmtypes.marine_sensor import radiometer_t
# downwelling_photon_spherical_irradiance mol m-2 s-1
# | downwelling_photon_flux_in_sea_water mol m-2 s-1
# | downwelling_photon_radiance_in_sea_water mol m-2 s-1 sr-1
# + bioluminescent_photon_rate_in_sea_water s-1 m-3


class BioluminescenceAverager:

    def __init__(self, npackets=200, verbose=0):
        self.lcm = lcm.LCM()
        self.npackets = npackets
        self.data = deque(maxlen=npackets)
        self.verbose = verbose

    def estimate_ambient(self,):
        """Estimate the ambient *downwelling_photon_spherical_irradiance*

        This does the heavly lifting.
        """
        return mean(self.data)

    def handler(self, channel, data):
        """receive scaled log counts and publish estimated irradiance
        """
        rx = radiometer_t.decode(data)
        self.data.append(rx.downwelling_photon_spherical_irradiance)
        if len(self.data) == self.data.maxlen:
            rx.downwelling_photon_spherical_irradiance = self.estimate_ambient()
            if self.verbose > 0:
                print(rx.downwelling_photon_spherical_irradiance)
            self.lcm.publish("{0}{1}mean".format(channel, self.npackets),
                rx.encode())
        else:
            print("input buffer not full: {0} < {1}".format(len(self.data),
                self.data.maxlen))

    def filter(self, channel='RAD2d200fir'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()


def main(channel='RAD2d200fir', verbose=0, packets=200):
    """Run as a daemon."""
    bf = BioluminescenceAverager(verbose=verbose, npackets=packets)
    bf.filter(channel)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LCM daemon to filter radiometer data")
    p.add_argument('-v', '--verbose', action='count', default=0,
                   help='display verbose output')
    p.add_argument('-V', '--version', action='version',
                   version='%(prog)s 0.0.1',
                   help='display version information and exit')
    p.add_argument('-c', '--channel', default='RAD2d200fir',
                   help='channel to listen on')
    p.add_argument('-p', '--packets', type=int, default=200,
                   help='number of packets in outer window')

    a = p.parse_args()
    main(**a.__dict__)
