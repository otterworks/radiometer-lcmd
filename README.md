Radiometer LCM Daemon
=====================

Prerequisites
-------------

- Install python3 and python3-pip.

- Install LCM with python3 bindings.

Install
-------

```shell
lcm-gen --python --ppath radiometer_lcmtypes radiometer_lcmtypes/*.lcm
python3 -m pip install . # to install the lcmtypes under `PYTHONPATH`
```

