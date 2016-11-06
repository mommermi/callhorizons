.. _examples:

Examples
--------

1. Find the hours on the night of 2015-10-25 (UT) when Centaur
   Echeclus is observable with airmass < 1.5 from Mauna Kea
   (observatory code: 568) during dark time::

     import callhorizons
     echeclus = callhorizons.query('echeclus')
     echeclus.set_epochrange('2015-10-25', '2015-10-26', '1h')
     echeclus.get_ephemerides(568)
     print(echeclus[(echeclus['solar_presence'] != 'daylight') & (echeclus['airmass'] < 1.5)]['datetime'])

   Note: you can also use HORIZONS' own ``skip daylight`` function and
   set an airmass limit during the query::

     echeclus.get_ephemerides(568, skip_daylight=True, airmass_lessthan=1.5)
     print(echeclus['datetime'])

2. Pull the orbital elements of Saturn on a specific date::

     import callhorizons
     saturn = callhorizons.query('Saturn', smallbody=False)
     saturn.set_discreteepochs('2451234.5')
     saturn.get_elements()

   This will cause a ``ValueError: Ambiguous target name; check URL:
   ...``. Why did that happen? Check out the URL that is provided
   with the error message; it will tell you the reason. The target
   name is ambiguous, since there is (the center of) Saturn and the
   barycenter of the Saturn system. If you are interested in the
   planet, use the ID number (699) instead of the planets name::

     import callhorizons
     saturn = callhorizons.query('699', smallbody=False)
     saturn.set_discreteepochs('2451234.5')
     saturn.get_elements()

3. more examples will come in the future ... (what are you interested in?)
