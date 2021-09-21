#!/usr/bin/env python3
"""

"""

import select
import serial
import struct
import time
import lcm

from collections import deque
from numpy import mean

from radiometer_lcmtypes.marine_sensor import radiometer_t
# downwelling_photon_spherical_irradiance mol m-2 s-1
# | downwelling_photon_flux_in_sea_water mol m-2 s-1
# | downwelling_photon_radiance_in_sea_water mol m-2 s-1 sr-1
# + bioluminescent_photon_rate_in_sea_water s-1 m-3


class RollingMeanFilter:

    def __init__(self, width=100, verbose=0):
        self.lcm = lcm.LCM()
        self.data = deque(maxlen=width)
        self.verbose = verbose

    def handler(self, channel, data):
        """receive scaled log counts and publish estimated irradiance
        """
        rx = radiometer_t.decode(data)
        self.data.append(rx.downwelling_photon_spherical_irradiance)
        if len(self.data) == self.data.maxlen:
            rx.downwelling_photon_spherical_irradiance = mean(self.data)
            if self.verbose > 0:
                print(rx.downwelling_photon_spherical_irradiance)
            tx_channel = "RAD2d200fir5mean" # TODO # This is TEMPORARY for 042
#            tx_channel = "{0}5mean".format(channel) # TODO let channel name change according to args
            self.lcm.publish(tx_channel, rx.encode())

    def filter(self, channel='RAD2d200iaf'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()


def main(channel='RAD2d200iaf', width=100, verbose=0):
    """Run as a daemon."""
    rmf = RollingMeanFilter(width=width, verbose=verbose)
    rmf.filter(channel);


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LCM daemon to filter radiometer data")
    p.add_argument('-v', '--verbose', action='count', default=0,
                   help='display verbose output')
    p.add_argument('-V', '--version', action='version',
                   version='%(prog)s 0.0.1',
                   help='display version information and exit')
    p.add_argument('-c', '--channel', default='RAD2d200iaf',
                   help='channel to listen on')
    p.add_argument('-w', '--width', type=int, default=100,
                   help='window width in ensembles [default 100, 5s]')

    a = p.parse_args()
    main(**a.__dict__)
