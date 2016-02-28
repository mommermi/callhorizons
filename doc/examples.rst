.. _examples:

Examples
--------

1. Find the hours on the night of 2015-10-25 (UT) if Centaur
   Echeclus is observable with airmass < 1.5 from Mauna Kea
   (observatory code: 568) during dark time::

     import callhorizons
     echeclus = callhorizons.query('echeclus')
     echeclus.set_epochrange('2015-10-25', '2015-10-26', '1h')
     echeclus.get_ephemerides(568)
     print echeclus[(echeclus['solar_presence'] != 'daylight') & (echeclus['airmass'] < 1.5)]['datetime']

   Note: you can also use HORIZONS' own ``skip daylight`` function and
   set an airmass limit during the query::

     echeclus.get_ephemerides(568, skip_daylight=True, airmass_lessthan=1.5)
     print echeclus['datetime']

   
2. more examples will come in the future ... (what are you interested in?)
