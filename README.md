Radiometer LCM Daemon
=====================

Prerequisites
-------------

- Install python3 and python3-pip.

- Install LCM with python3 bindings.

- Install pyserial and linuxfd from pip.

  *TODO*: ^do this^ with `requirements.txt`


You may need to adjust `PYTHONPATH` so that python can find LCM.
and the

Install
-------

```shell
lcm-gen --python --ppath radiometer_lcmtypes radiometer_lcmtypes/*.lcm
python3 -m pip install . # to install the lcmtypes under `PYTHONPATH`
```

*TODO* Reorganize to install the daemons under `PYTHONPATH` as well.

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

ToDo
----

Refactor into a FOLRadiometer class with the scaling, descaling, struct defs,
then use that to rewrite the lcmd and spoof executables.

Put 1 Hz summer into base daemon (to avoid issues when network is overloaded).
