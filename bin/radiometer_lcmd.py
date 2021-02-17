#!/usr/bin/env python3
"""flowmeter_can_lcmd - LCM daemon for flow meter."""

import select
import serial
import struct
import time
import lcm

from mesobot_lcmtypes.raw import bytes_t


class RadiometerDaemon:
    """LCM daemon for radiometer."""

    def __init__(self, dev='/dev/ttyUSB1', prefix='RAD'):
        """Define serial and LCM interfaces, and subscribe to input."""
        self.serial = serial.Serial(dev, baudrate=38400, timeout=0.1)
        self.lcm = lcm.LCM()
        self.prefix = prefix
        self.hdr = struct.Struct('<H') # one uint16
        self.clkpkt = struct.Struct('<H2L') # 2 unsigned long bytes (ISR clock cycles, LOG clock cycles)
        self.hrtpkt = struct.Struct('<H5L') # 5 unsigned long bytes (UTC, Pulse count, nsHI, irradiance, end token)
        self.datpkt = struct.Struct('<HL50H')

        self.subscriptions = []
        self.subscriptions.append(self.lcm.subscribe(
            '{0}i'.format(self.prefix), self.lcm_handler))

    def lcm_handler(self, channel, data):
        """Receive command on LCM and send over serial port.

        Initially, this will pass opaque byte streams.
        Later, we may refactor for more user-friendly LCM messages.
        """
        rx = raw.bytes_t.decode(data)
        print("rx on LCM {0}: {1}".format(channel, rx.data))
        self.serial.write(rx.data)
        self.serial.flush()

    def serial_handler(self):
        """Receive data on serial port and send on LCM."""
        hdr = self.serial.read(2)
        if hdr is None:
            print('tried to handle empty serial message queue')
        elif len(hdr) == 2 and self.hdr.unpack(hdr) == 0xFF: # clock packet
            rx = self.serial.read(self.clkpkt.size)
            (h, ISR, LOG) = self.clkpkt.unpack(rx)
            print("ISR: {0}, LOG: {1}".format(ISR,LOG))
            # self.lcm.publish("{0}_hdr".format(self.prefix), head.encode())
        elif len(hdr) == 2 and self.hdr.unpack(hdr) == 0xFE: # heartbeat
            print('rx heartbeat message')
            rx = self.serial.read(self.hrtpkt.size)
            hbval = self.hbpkt.unpack(rx)
            print("{0}\n".format(hbval))
            # self.lcm.publish("{0}_hb".format(self.prefix), heartbeat.encode())
        else: # shouldn't we have a positive identifier, according to Jan15 email?
            rx = self.serial.read(self.datpkt.size)
            if(len(rx) != self.datpkt.size):
                print("unknown header: {0:x}".format(hdr))
                self.serial.flushInput()
            else:
                tx = bytes_t()
                tx.utime = int(time.time() * 1e6)
                tx.length = self.datpkt.size + self.hdr.size
                tx.data = hdr + rx
                self.lcm.publish("{0}o".format(self.prefix), tx.encode())

    def connect(self):
        """Connect serial to LCM and loop with epoll."""
        epoll = select.epoll()
        epoll.register(self.lcm.fileno(), select.EPOLLIN)
        epoll.register(self.serial.fileno(), select.EPOLLIN)
        try:
            while True:
                for fileno, _events in epoll.poll(1):
                    if fileno == self.lcm.fileno():
                        self.lcm.handle()
                    elif fileno == self.serial.fileno():
                        self.serial_handler()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
        finally:
            epoll.unregister(self.serial.fileno())
            epoll.unregister(self.lcm.fileno())
            epoll.close()


def main(dev="/dev/ttyUSB1", prefix='RAD', verbose=0):
    """Run as a daemon."""
    bridge = RadiometerDaemon(dev, prefix)
    bridge.connect()


if __name__ == "__main__":
    import argparse
    P = argparse.ArgumentParser(description="LCM daemon for radiometer")
    P.add_argument('-v', '--verbose', action='count', default=0,
                   help='display verbose output')
    P.add_argument('-V', '--version', action='version',
                   version='%(prog)s 0.0.1',
                   help='display version information and exit')
    P.add_argument('dev', help='the serial device to use')
    P.add_argument('-p', '--prefix', default='RAD',
                   help='prefix to pub/sub with')
    A = P.parse_args()
    main(**A.__dict__)
