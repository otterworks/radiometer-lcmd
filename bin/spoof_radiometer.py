#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import select
import serial
import struct

import linuxfd


class SpoofedRadiometer(serial.Serial):
    """Test class to emulate radiometer publishing data on serial port.

    """

    def __init__(self, **kw):
        """initialize serial port

        This method includes defaults to match the configuration of the
        radiometer as specified and installed on mesobot.

        """
        if 'port' not in kw:
            kw['port'] = '/dev/ttyUSB1'
        if 'baudrate' not in kw:
            kw['baudrate'] = 115200
        if 'bytesize' not in kw:
            kw['bytesize'] = 8
        if 'parity' not in kw:
            kw['parity'] = 'N'
        if 'stopbits' not in kw:
            kw['stopbits'] = 1
        if 'timeout' not in kw:
            kw['timeout'] = 0.1
        if 'xonxoff' not in kw:
            kw['xonxoff'] = 0
        if 'rtscts' not in kw:
            kw['rtscts'] = 0

        self.pkt = struct.Struct('!HH')

        super(SpoofedRadiometer, self).__init__(**kw)


    def publish(self, count=1, duration=1):
        self.write(self.pkt.pack(count, duration))
        self.flush()

    def serve(self, frequency=1000):
        """Publish periodic sample data

        """
        epoll = select.epoll()
        tfd = linuxfd.timerfd()
        tfd.settime(1.0/frequency, 1.0/frequency)
        epoll.register(tfd.fileno(), select.EPOLLIN)
        try:
            while 1 <3:
                events = epoll.poll(1)
                for fileno, event in events:
                    if fileno == tfd.fileno():
                        self.publish()
                    else:
                        print('unexpected file #: {0}'.format(fileno))
        except KeyboardInterrupt:
            print('Stopped by CTRL-C')
        finally:
            epoll.unregister(tfd.fileno())
            epoll.close()
            self.close()


if __name__ == '__main__':
    import argparse
    P = argparse.ArgumentParser(description="LCM daemon for radiometer")
    P.add_argument('-f', '--frequency', default=1000, type=int,
                   help='frequency to publish data')
    P.add_argument('dev', help='the serial device to use')
    A = P.parse_args()
    spoofer = SpoofedRadiometer(port=A.dev)
    spoofer.serve(frequency=A.frequency)
