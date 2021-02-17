#!/usr/bin/env python3
"""flowmeter_can_lcmd - LCM daemon for flow meter."""

import select
import serial
import struct
import time
import lcm

from collections import deque

from mesobot_lcmtypes.raw import bytes_t


class RadiometerDaemon:
    """LCM daemon for radiometer."""

    def __init__(self, dev='/dev/ttyUSB1', prefix='RAD'):
        """Define serial and LCM interfaces, and subscribe to input."""
        self.serial = serial.Serial(dev, baudrate=38400, timeout=0.1)
        self.lcm = lcm.LCM()
        self.prefix = prefix
        self.hdr = deque(maxlen = 4)
        self.hrtpkt = struct.Struct('<5L') # 5 unsigned long bytes (UTC, Pulse count, nsHI, irradiance, end token)
        self.datpkt = struct.Struct('<2L50H') # 2 unsigned long bytes (ISR clock cycles, LOG clock cycles)

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
        self.hdr.clear()
        self.hdr.extend(self.serial.read(4))
        while(self.serial.in_waiting > 0):
            # assert (len(self.hdr) == self.hdr.maxlen), "header too short"
            bsh = bytes(self.hdr)
            if bsh == b'\x00\xff\x00\xff':
                suffix = 'o'
                pkt_size = self.datpkt.size
            elif bsh == b'\x00\xfe\x00\xfe':
                suffix = 'h'
                pkt_size = self.hrtpkt.size
            else:
                suffix = 'r'
                pkt_size = 0
                print(bytes(self.hdr).hex(' '))

            self.handle_pkt(suffix, pkt_size)
            if pkt_size == 0:
                print(' <<=')
                self.hdr.extend(self.serial.read(1))
                print(bytes(self.hdr).hex(' '))
                print('____')

    def handle_pkt(self, suffix='r', sz=108):
        rx = self.serial.read(sz)
        if(len(rx) == sz):
            tx = bytes_t()
            tx.utime = int(time.time() * 1e6)
            tx.length = len(self.hdr) + sz
            tx.data = bytes(self.hdr) + rx
            self.lcm.publish("{0}{1}".format(self.prefix, suffix), tx.encode())
        else:
            print('tried to read {0} but only got {1}'.format(sz, len(rx)))

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
