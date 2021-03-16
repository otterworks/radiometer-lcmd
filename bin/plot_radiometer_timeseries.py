#!/usr/bin/env python3

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from lcm import EventLog

from mesobot_lcmtypes.raw import floats_t
from mesobot_lcmtypes.marine_sensor import radiometer_t, pressure_depth_t
# ^ TODO use radiometer_lcmtypes instead...

el = EventLog('/wdb/mesobot/2021-02.Bermuda/logs/mesobot037.lcmlog','r')

depth = [pressure_depth_t.decode(evt.data).depth for evt in el if evt.channel == "DQo"]
depth_utime = (pressure_depth_t.decode(evt.data).utime for evt in el if evt.channel == "DQo")
depth_datetime = [datetime.utcfromtimestamp(usec/1e6) for usec in depth_utime]

rad = np.array([floats_t.decode(evt.data).data for evt in el if evt.channel == "RAD2d"]).ravel()
wtime = np.arange(-49e3,1e3,1e3)
rad_utime = np.array([floats_t.decode(evt.data).utime + wtime for evt in el if evt.channel == "RAD2d"]).ravel()
rad_datetime = [datetime.utcfromtimestamp(usec/1e6) for usec in rad_utime]

rad10 = rad[:int(rad.shape[0]/10)*10].reshape(-1, 10).sum(axis=1)
rad10_datetime = rad_datetime[:int(rad.shape[0]/10)*10:10]
rad100 = rad10[:int(rad10.shape[0]/10)*10].reshape(-1, 10).sum(axis=1)
rad100_datetime = rad10_datetime[:int(rad10.shape[0]/10)*10:10]
rad1000 = rad100[:int(rad100.shape[0]/10)*10].reshape(-1, 10).sum(axis=1)
rad1000_datetime = rad100_datetime[:int(rad100.shape[0]/10)*10:10]

fig, rax = plt.subplots(4, 1, sharex = True)
dax = []
for ax in rax:
    dax.append(ax.twinx())
for ax in dax:
    ax.plot(depth_datetime, depth, color='black')
    ax.set_ylabel('depth [m]')
    ax.invert_yaxis()
rax[0].scatter(rad_datetime, np.log10(rad), s=1, c='blue')
rax[0].set_ylabel(r'log10(photon/ms)')
rax[1].scatter(rad10_datetime, np.log10(rad10), s=1, c='blue')
rax[1].set_ylabel(r'log10(photon/10ms)')
rax[2].scatter(rad100_datetime, np.log10(rad100), s=1, c='blue')
rax[2].set_ylabel(r'log10(photon/100ms)')
rax[3].scatter(rad1000_datetime, np.log10(rad1000), s=1, c='blue')
rax[3].set_ylabel(r'log10(photon/s)')

plt.show()

"""
if __name__ == '__main__':
    import argparse

    main()
"""
