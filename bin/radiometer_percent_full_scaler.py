#!/usr/bin/env python3
"""

"""

import select
import serial
import struct
import time
import lcm

from numpy import array

from radiometer_lcmtypes.raw import floats_t


class PercentFullScaler:

    def __init__(self, verbose=0):
        self.lcm = lcm.LCM()
        self.verbose = verbose

    def handler(self, channel, data):
        """receive time high and publish percent 
        """
        rx = floats_t.decode(data)
        rx.data = 1e-4 * array(rx.data);
        self.lcm.publish("{0}p".format(channel[:4]), rx.encode())

    def filter(self, channel='RAD1t'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()


def main(channel='RAD1t', verbose=0):
    """Run as a daemon."""
    pfs = PercentFullScaler(verbose=verbose)
    pfs.filter(channel);


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LCM daemon to filter radiometer data")
    p.add_argument('-v', '--verbose', action='count', default=0,
                   help='display verbose output')
    p.add_argument('-V', '--version', action='version',
                   version='%(prog)s 0.0.1',
                   help='display version information and exit')
    p.add_argument('-c', '--channel', default='RAD1t',
                   help='channel to listen on')

    a = p.parse_args()
    main(**a.__dict__)
