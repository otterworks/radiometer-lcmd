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

from radiometer_lcmtypes.raw import floats_t
from radiometer_lcmtypes.marine_sensor import radiometer_t
# downwelling_photon_spherical_irradiance mol m-2 s-1
# | downwelling_photon_flux_in_sea_water mol m-2 s-1
# | downwelling_photon_radiance_in_sea_water mol m-2 s-1 sr-1
# + bioluminescent_photon_rate_in_sea_water s-1 m-3


class IsoluminanceAveragerFilter:

    def __init__(self, width=200, verbose=0):
        self.lcm = lcm.LCM()
        self.data = deque(maxlen=width)
        self.verbose = verbose

    def estimate_ambient(self):
        """Estimate the ambient *downwelling_photon_spherical_irradiance*

        This does the heavly lifting.
        """
        tosort = list(self.data.copy())
        tosort.sort()
        # assert len(filtered) == ntaps + 1
        x = sum(tosort[:20])
        x -= 800
        if x < 2:
            x = 2
        return float(x)


    def handler(self, channel, data):
        """receive scaled log counts and publish estimated irradiance
        """
        rx = floats_t.decode(data)
        self.data.append(sum(rx.data))
        if len(self.data) == self.data.maxlen:
            tx = radiometer_t()
            tx.utime = rx.utime
            tx.downwelling_photon_spherical_irradiance = self.estimate_ambient()
            if self.verbose > 0:
                print(tx.downwelling_photon_spherical_irradiance)
            # tx_channel = "{0}{1}mm".format(channel, self.data.maxlen)
            tx_channel = "RAD2d200iaf"
            self.lcm.publish(tx_channel, tx.encode())
        elif self.verbose > -1:
            print("window not full: {0} < {1}".format(len(self.data),
                self.data.maxlen))

    def filter(self, channel='RAD2d'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()


def main(channel='RAD2d', width=200, verbose=0):
    """Run as a daemon."""
    iaf = IsoluminanceAveragerFilter(width=width, verbose=verbose)
    iaf.filter(channel);


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
    p.add_argument('-w', '--width', type=int, default=200,
                   help='window width in ensembles')

    a = p.parse_args()
    main(**a.__dict__)
