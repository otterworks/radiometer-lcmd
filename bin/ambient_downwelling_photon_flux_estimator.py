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

SAMPLES_PER_ENSEMBLE = 50
DEFAULT_SORT_WIDTH = 200 # 200 ensembles @ 20 Hz ==> 10s
DEFAULT_SUM_WIDTH = 20 # 20 ensembles @ 20 Hz ==> 1s


class AmbientDownwellingPhotonFluxEstimator:

    def __init__(self, suffix = 'u', width=DEFAULT_SORT_WIDTH, verbose=0):
        self.lcm = lcm.LCM()
        self.data = deque(maxlen=width*SAMPLES_PER_ENSEMBLE)
        self.suffix = suffix
        self.verbose = verbose

    def estimate_ambient(self):
        """Estimate the ambient *downwelling_photon_spherical_irradiance*

        This does the heavy lifting.
        """
        tosort = list(self.data.copy())
        tosort.sort()
        amb = float(sum(tosort[:DEFAULT_SUM_WIDTH*SAMPLES_PER_ENSEMBLE]))
        return max([amb, 1e-16]) # make output log10-safe

    def handler(self, channel, data):
        rx = floats_t.decode(data)
        self.data.extend(rx.data)
        if len(self.data) == self.data.maxlen:
            tx = radiometer_t()
            tx.utime = rx.utime
            tx.downwelling_photon_spherical_irradiance = self.estimate_ambient()
            if self.verbose > 0:
                print(tx.downwelling_photon_spherical_irradiance)
            tx_channel = "{0}{1}".format(channel[:4], self.suffix)
            self.lcm.publish(tx_channel, tx.encode())
        elif self.verbose > -1:
            print("window not full: {0} < {1}".format(len(self.data),
                self.data.maxlen))

    def filter(self, channel='RAD1fd'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()


def main(channel='RAD1fd', suffix='u', width=DEFAULT_SORT_WIDTH, verbose=0):
    """Run as a daemon."""
    est = AmbientDownwellingPhotonFluxEstimator(suffix=suffix, width=width, verbose=verbose)
    est.filter(channel);


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LCM daemon to filter radiometer data")
    p.add_argument('-v', '--verbose', action='count', default=0,
                   help='display verbose output')
    p.add_argument('-V', '--version', action='version',
                   version='%(prog)s 0.0.1',
                   help='display version information and exit')
    p.add_argument('-c', '--channel', default='RAD1fd',
                   help='channel to listen on')
    p.add_argument('-s', '--suffix', default='u',
                   help='suffix for filter output')
    p.add_argument('-w', '--width', type=int, default=DEFAULT_SORT_WIDTH,
                   help='window width in ensembles')

    a = p.parse_args()
    main(**a.__dict__)
