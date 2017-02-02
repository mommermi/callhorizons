How to Use It?
--------------

1. import the module into your code::

     import callhorizons
      
2. initialize a QUERY object with an objectname that is readable by
   the `JPL HORIZONS`_ website; this might be the target asteroid's name::

     dq = callhorizons.query('Don Quixote')

   number::

     dq = callhorizons.query('3552')

   name and number::

     dq = callhorizons.query('(3552) Don Quixote')
     
   designation::

     dq = callhorizons.query('1983 SA')

   or packed designation::

     dq = callhorizons.query('J83S00A')

   **Comet** names may be the full periodic number and name::

     dq = callhorizons.query('1P/Halley')
     dq = callhorizons.query('3D/Biela')

   periodic number only::

     dq = callhorizons.query('9P')

   orbit solution ID::

     dq = callhorizons.query('900190')
     
   temporary designation::

     dq = callhorizons.query('P/2001 YX127')

   temporary designation with name::

     dq = callhorizons.query('P/1994 N2 (McNaught-Hartley)')

   or long period / hyperbolic comet designation, with or without name::

     dq = callhorizons.query('C/2013 US10 (Catalina)')     
     dq = callhorizons.query('C/2012 S1')

   Fragments may also be requested::
  
     dq = callhorizons.query('C/2001 A2-A')
     dq = callhorizons.query('73P-C/Schwassmann Wachmann 3 C')

   but note that the name is ignored.  The following will not return
   fragment B, but instead the ephemeris for 73P (compare with the
   previous example)::

     dq = callhorizons.query('73P/Schwassmann Wachmann 3 B')

   By default, comet queries will return the most recent or current
   apparition (HORIZONS's 'CAP' parameter).  This behavior can be
   disabled with the `cap=False` keyword argument::

     dq = callhorizons.query('9P', cap=False)

   If there are multiple orbit solutions available, CALLHORIZONS will
   raise a ``ValueError`` and provide the URL with explanations.

   You can also query **major bodies** (planets and moons) and
   **spacecraft**. This is a little bit trickier, since there are no
   clear naming conventions for these objects, causing ambiguities
   (see the `Horizons documentation`_ for a discussion). Assume that
   we want to select Jupiter's moon Io, we would could use the
   following line::

     io = callhorizons.query('Io', smallbody=False)
   
   Please note the flag ``smallbody=False``, which is necessary
   here. However, this line will cause an error when one tries to
   obtain ephemerides or orbital elements: ``ValueError: Ambiguous
   target name; check URL: http://ssd.jpl.nasa.gov/...``. Calling the
   provided URL explains the problem. Horizons selects all known
   objects that contain the letters `io`. In order to unambiguously
   refer to Jupiter's moon Io, one has to use the provided ID number,
   which is 501. Hence, one should use::

     io = callhorizons.query(501, smallbody=False)

   Every target listed in Horizons provides an ID number, allowing for
   unambiguous identification. If there is ambiguity - or if the
   target is not in the Horizons database - CALLHORIZONS
   will raise a ``ValueError`` and provide the URL with
   explanations. Spacecraft can be selected the same way, also
   requiring the ``smallbody=False`` flag.

     
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
  dq.query    # show URL to query Horizons

Queried data can also be filtered, e.g., based on airmass::

  dq[dq['airmass'] < 1.5]

Orbital elements queried with CALLHORIZONS can be directly converted
into PyEphem objects to calculate the ephemerides::

  import ephem
  dq.get_elements()
  dq_pyephem = dq.export2pyephem()
  
Once ephemerides or orbital elements have been queried, the URL with
which HOrizons has been called can be listed::

  print(dq.query)

This is especially useful for debugging and finding out why a query
might have failed.
  
For more information, see the :doc:`examples` and the :doc:`modules` reference.


.. _JPL HORIZONS: http://ssd.jpl.nasa.gov/horizons.cgi
.. _Horizons documentation: http://ssd.jpl.nasa.gov/?horizons_doc#selection
