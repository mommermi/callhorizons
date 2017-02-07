CALLHORIZONS - a Python Interface to JPL HORIZONS
=================================================

Overview
--------

This module provides a convenient python interface to the JPL HORIZONS
system by directly accessing and parsing the http website. Ephemerides
can be obtained through `get_ephemerides`, orbital elements through
`get_elements`. Function `export2pyephem` provides a convenient
interface to the PyEphem module that allows for ephemerides
calculations on your machine.


Installation
------------

The easiest way is to install the module using pip::

  pip install callhorizons

For other ways, see the `documentation`_.


Documentation
-------------

The CALLHORIZONS documentation is available at http://mommermi.github.io/callhorizons/readme.html 


Examples
--------

* print RA and DEC of asteroid 433 Eros from Mauna Kea for two
  discrete dates::

    import callhorizons
    eros = callhorizons.query('Eros')
    eros.set_discreteepochs([2457446.177083, 2457446.182343])
    eros.get_ephemerides(568)
    print eros['RA'], eros['DEC']

For more examples, see the `documentation`_.
    

License
-------

This code is published under the MIT License. Feel free to use this
code and modify it to your own needs. Please note that the code is
provided as is, without any warranty (see LICENSE file for details).

Copyright (c) 2016 Michael Mommert


Contact
-------

Feel free to contact me with your suggestions and comments!

michael.mommert (at) nau.edu


Changelog
---------

* 2017-02-07: better support for target name parsing (thanks to `mkelley`_!)

* 2016-11-08: added ObsEclLon and ObsEclLat to get_ephemerides()

* 2016-11-06: implemented tests and Python 3.5 support, v1.0.2

* 2016-09-12: bugfix in get_elements, v1.0.1

* 2016-07-19: implemented query for non-asteroidal objects (planets and satellits), v1.0

* 2016-01-13: implemented function export2pyephem that exports orbital
  elements into a PyEphem object
  (requires PyEphem: http://rhodesmill.org/pyephem/)

* 2016-02-27: changed structure into class structure, created pip installer, v1.0

.. _documentation: http://mommermi.github.io/callhorizons/readme.html
.. _mkelley: https://github.com/mkelley
