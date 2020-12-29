Radiometer LCM Daemon
=====================

Prerequisites
-------------

Install [mesobot-lcmtypes] 0.2.9 or later. Be sure to install the python
package (e.g., with `make pip-install`).

You may need to adjust `PYTHONPATH` so that python can find LCM and the
types package.

Testing
-------

On the tx2, start the (draft) LCM daemon:
```shell
./bin/radiometer_lcmd.py /dev/ttyUSB1
```


On an external machine, spoof the radiometer measurement data:

```shell
./bin/spoof_radiometer.py -f 1000 /dev/ttyUSB0
```

and if the external machine is connected to the same multicast network, you
can see the data on lcm using `mesobot-spy`.

```shell
mesobot-spy # will open a java GUI
```

[mesobot-lcmtypes]: https://bitbucket.org/whoidsl/mesobot-lcmtypes
