#!/usr/bin/env python3
"""radiometer_lcmd - LCM daemon for radiometer."""

import select
import serial
import struct
import time
import lcm

from collections import deque

from radiometer_lcmtypes.raw import bytes_t, floats_t


class RadiometerDaemon:
    """LCM daemon for radiometer."""

    def __init__(self, dev='/dev/ttyUSB1', prefix='RAD'):
        """Define serial and LCM interfaces, and subscribe to input."""
        self.postmultiplier = (2**16)/7.0
        self.serial = serial.Serial(dev, baudrate=38400, timeout=1)
        self.lcm = lcm.LCM()
        self.prefix = prefix + dev[-1]
        self.tkn = deque(maxlen = 4)
        self.heartbeat = struct.Struct('<7L') # 7 uint32 (UTC, millis, Pulse count, nsHI, irradiance, inclinometer, end token)
        self.data = struct.Struct('<2L50H') # 2 uint32 (ISR clock cycles, LOG clock cycles), then 50 uint16

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
        pkt_size = 0
        self.tkn.extend(self.serial.read(self.tkn.maxlen))
        while pkt_size == 0:
            bsh = bytes(self.tkn)
            if bsh == bytes.fromhex('00800080'):
                suffix = 'o'
                pkt_size = self.data.size
            elif bsh == bytes.fromhex('11811181'):
                suffix = 'h'
                pkt_size = self.heartbeat.size
            else:
                suffix = 'r'
                pkt_size = 0
            self.handle_pkt(suffix, pkt_size)
            if pkt_size == 0 and self.serial.in_waiting > 0:
                self.tkn.extend(self.serial.read(1))

    def handle_pkt(self, suffix='r', sz=0):
        rx = self.serial.read(sz)
        if(len(rx) == sz):
            tx = bytes_t()
            tx.utime = int(time.time() * 1e6)
            tx.length = len(self.tkn) + sz
            tx.data = bytes(self.tkn) + rx
            self.lcm.publish("{0}{1}".format(self.prefix, suffix), tx.encode())
            if(suffix == 'o' and sz == self.data.size):
                self.publish(tx)
        else:
            print('tried to read {0} but only got {1}'.format(sz, len(rx)))

    def publish(self, raw, suffix='t'):
        tx = floats_t()
        tx.utime = raw.utime
        b = raw.data[4:] # assert len(b) = self.data.size
        tx.data = self.data.unpack(b)[2:] # skip the extras
        tx.length = len(tx.data) # assert = 50
        self.lcm.publish("{0}{1}".format(self.prefix, suffix), tx.encode())

    def connect(self):
        """Connect serial to LCM and loop with epoll."""
        epoll = select.epoll()
        epoll.register(self.lcm.fileno(), select.EPOLLIN)
        epoll.register(self.serial.fileno(), select.EPOLLIN)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
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
