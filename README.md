Radiometer LCM Daemon
=====================

Prerequisites
-------------

Install [mesobot-lcmtypes] 0.2.10 or later on the tx2.
Be sure to install the python package (e.g., with `make pip-install`).

You may need to adjust `PYTHONPATH` so that python can find LCM and the
types package.

Install python3, pyserial, and linuxfd from pip on the external machine.

Install [mesobot-lcmtypes] 0.2.10 or later on the external machine if you
want to see decodeable data on `mesobot-spy`.

Testing
-------

On the tx2, start the (draft) LCM daemon:
```shell
export LCM_DEFAULT_URL=udpm://239.255.76.67:7667?ttl=1
./bin/radiometer_lcmd.py /dev/ttyUSB1
```

And in another session on the tx2, start the (draft) bioluminescence filter:
```shell
export LCM_DEFAULT_URL=udpm://239.255.76.67:7667?ttl=1
./bin/bioluminescence_filter_lcmd.py
```

Plug in the radiometer tester circuit from Jacob, picocom into the teensy,
and press `l` (lowercase L) to start it sending data.

and if the external machine is connected to the same multicast network, you
can see the data on lcm using `mesobot-spy`.

```shell
mesobot-spy # will open a java GUI
```

[mesobot-lcmtypes]: https://bitbucket.org/whoidsl/mesobot-lcmtypes
