How to Use It?
--------------

1. import the module into your code::

     import callhorizons
      
2. initialize a QUERY object with an objectname that is readable by
   the `JPL HORIZONS`_ website; this might be the target's name::

     dq = callhorizons.query('Don Quixote')

   number::

     dq = callhorizons.query('3552')

   designation::

     dq = callhorizons.query('1983 SA')

   or packed designation::

     dq = callhorizons.query('J83S00A')

3. set the time range of epochs that you want to query using::

     dq.set_epochrange('2016-02-27 03:20', '2016-02-28 05:20', '1h')

   where the order is `start date and time`, `end date and time`, and
   `step size` using `YYYY-MM-DD HH:MM` UT times, or set discrete
   times::

     dq.set_discreteepochs([2457446.177083, 2457446.182343])

   where up to 15 discrete epochs are provided in the form of a list of
   Julian Dates.

4. query ephemerides for the given times for a given observatory code
   (here: 568, Mauna Kea)::

     dq.get_ephemerides(568)

   or, obtain the target's orbital elements::

     dq.get_elements()


The queried data are stored in the `QUERY` object and can be accessed
easily::

  dq.fields   # provide list of available target properties
  dq['RA']    # access 'RA' for all epochs
  dq[0]       # access all properties for the first epoch
  dq.dates    # provide list of epochs

Queried data can also be filtered, e.g., based on airmass::

  dq[dq['airmass'] < 1.5]

Orbital elements queried with CALLHORIZONS can be directly converted
into PyEphem objects to calculate the ephemerides::

  import ephem
  dq.get_elements()
  dq_pyephem = dq.export2pyephem()
  
  
For more information, see the :doc:`examples` and the :doc:`modules` reference.


.. _JPL HORIZONS: http://ssd.jpl.nasa.gov/horizons.cgi

