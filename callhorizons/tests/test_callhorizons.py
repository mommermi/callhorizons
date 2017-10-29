import callhorizons
import numpy as np

def agrees(x, y, eps=1e-5):
    if x != 0:
        return np.abs(x-y)/np.abs(x) < eps
    else:
        return np.abs(y) < eps


def test_ephemerides():
    """ check ephemerides output for one asteroid """

    asteroid_targetname = 'Ceres'
    target = callhorizons.query(asteroid_targetname)

    target.set_discreteepochs([2451544.500000])
    target.get_ephemerides(568)
        
    # compare all query results to values taken directly from Horizons
    # queried on Nov 6, 2016
    assert target['targetname'][0] == u'1 Ceres', target['targetname'][0]
    assert agrees(target['H'][0], 3.34), target['H'][0]
    assert agrees(target['G'][0], 0.12), target['G'][0]
    assert target['datetime'][0] == u'2000-Jan-01 00:00:00.000', \
        target['datetime'][0]
    assert agrees(target['datetime_jd'][0], 2451544.5), target['datetime_jd'][0]
    assert target['solar_presence'][0] == 'daylight', \
        target['solar_presence'][0]
    assert target['lunar_presence'][0] == 'dark', target['lunar_presence'][0]
    assert agrees(target['RA'][0], 188.70187), target['RA'][0]
    assert agrees(target['DEC'][0], 9.09786), target['DEC'][0]
    assert agrees(target['RA_rate'][0], 0.00967404166667), target['RA_rate'][0]
    assert agrees(target['DEC_rate'][0], -2.82060/3600), target['DEC_rate'][0]
    assert agrees(target['AZ'][0], 288.3275), target['AZ'][0]
    assert agrees(target['EL'][0], -20.5230), target['EL'][0]
    assert np.isnan(target['airmass'][0])
    assert np.isnan(target['magextinct'][0])
    assert agrees(target['V'][0], 8.27), target['V'][0]
    assert agrees(target['illumination'][0], 96.171), target['illumination'][0] 
    assert agrees(target['EclLon'][0], 161.3828), target['EclLon'][0]
    assert agrees(target['EclLat'][0], 10.4528), target['EclLat'][0]
    assert agrees(target['r'][0], 2.551098889601), target['r'][0]
    assert agrees(target['r_rate'][0], 0.1744499), target['r_rate'][0]
    assert agrees(target['delta'][0], 2.26316614786857), target['delta'][0]
    assert agrees(target['delta_rate'][0], -21.5499080), target['delta_rate'][0]
    assert agrees(target['lighttime'][0], 18.822179*60), target['lighttime'][0]
    assert agrees(target['elong'][0], 95.3997), target['elong'][0]
    assert target['elongFlag'][0] == u'leading', target['elongFlag'][0]
    assert agrees(target['alpha'][0], 22.5690), target['alpha'][0]
    assert agrees(target['sunTargetPA'][0], 292.552), target['sunTargetPA'][0]
    assert agrees(target['velocityPA'][0], 296.849), target['velocityPA'][0]
    assert agrees(target['GlxLon'][0], 289.861684), target['GlxLon'][0]
    assert agrees(target['GlxLat'][0], 71.545053), target['GlxLat'][0]
    assert agrees(target['RA_3sigma'][0], 0.0), target['RA_3sigma'][0]
    assert agrees(target['DEC_3sigma'][0], 0.0), target['DEC_3sigma'][0]


def test_elements():
    """ check orbital elements output for one moon """

    moon_targetname = 501
    target = callhorizons.query(moon_targetname, smallbody=False)

    target.set_epochrange('2000-01-01', '2000-01-02', '1d')
    target.get_elements('500@5')   # elements relative to Jupiter barycenter

    # compare all query results to values taken directly from Horizons
    # queried on Nov 6, 2016
    assert target['targetname'][0]   == 'Io (501)'
    assert np.isnan(target['H'][0])
    assert np.isnan(target['G'][0])
    assert agrees(target['datetime_jd'][0], 2451544.5), target['datetime_jd'][0]
    assert agrees(target['e'][0], 0.003654784965339888), target['e'][0]
    assert agrees(target['p'][0], 2.811473523687107E-03), target['p'][0]
    assert agrees(target['a'][0], 2.821786546733507E-03), target['a'][0]
    assert agrees(target['incl'][0], 2.212609179741271E+00), target['i'][0]
    assert agrees(target['node'][0], 3.368501231726219E+02), target['node'][0]
    assert agrees(target['argper'][0] ,6.218469675691234E+01), \
        target['argper'][0]
    assert agrees(target['Tp'][0], 2451545.103514090180), target['Tp'][0]
    assert agrees(target['meananomaly'][0], 2.373891296290639E+02), \
        target['meananomaly'][0]
    assert agrees(target['trueanomaly'][0], 2.370372158041970E+02), \
        target['trueanomaly'][0]
    assert agrees(target['period'][0], 1.771988665071993/365.256), \
        target['period'][0]
    assert agrees(target['Q'][0], 2.832099569779908E-03), target['Q'][0]


def test_pyephem():
    """ test PyEphem interface, if PyEphem is available """
    
    try:
        import ephem
    except ImportError:
        return None

    asteroid_targetname = 'Ceres'
    target = callhorizons.query(asteroid_targetname)

    target.set_discreteepochs([2451544.500000])

    # create pyephem object and calculate ra and dec for a given date
    ephobj = target.export2pyephem()[0]
    ephobj.compute('2000-01-10')
    # retrieve astrometric geocentric coordinates
    ephem_ra  = np.rad2deg(ephobj.a_ra)
    ephem_dec = np.rad2deg(ephobj.a_dec)
    ephem_mag = ephobj.mag
    
    # query horizons for exact positions and check if residuals are negligible
    # i.e., less than 0.5 arcsec
    target = callhorizons.query(asteroid_targetname)
    target.set_discreteepochs([2451553.5])
    target.get_ephemerides(500)

    assert ((target['RA'][0]-ephem_ra)*3600) < 0.1
    assert ((target['DEC'][0]-ephem_dec)*3600) < 0.1
    assert (target['V'][0]-ephem_mag) < 0.1


def test_designations():
    """Test comet and asteroid name to designation transformations."""

    # name: expected result
    comets = {
        '1P/Halley': (None, '1P', 'Halley'),
        '3D/Biela': (None, '3D', 'Biela'),
        '9P/Tempel 1': (None, '9P', 'Tempel 1'),
        '73P/Schwassmann Wachmann 3 C': (None, '73P',
                                         'Schwassmann Wachmann 3 C'),
        '73P-C/Schwassmann Wachmann 3 C': (None, '73P-C',
                                         'Schwassmann Wachmann 3 C'),
        '73P-BB': (None, '73P-BB', None),
        '322P': (None, '322P', None),
        'X/1106 C1': ('1106 C1', 'X', None),
        'P/1994 N2 (McNaught-Hartley)': ('1994 N2', 'P',
                                         'McNaught-Hartley'),
        'P/2001 YX127 (LINEAR)': ('2001 YX127', 'P', 'LINEAR'),
        'C/-146 P1': ('-146 P1', 'C', None),
        'C/2001 A2-A (LINEAR)': ('2001 A2-A', 'C', 'LINEAR'),
        'C/2013 US10': ('2013 US10', 'C', None),
        'C/2015 V2 (Johnson)': ('2015 V2', 'C', 'Johnson')
    }

    asteroids = {
        '1': (None, 1, None),
        '(2) Pallas': (None, 2, 'Pallas'),
        '(2001) Einstein': (None, 2001, 'Einstein'), 
        '2001 AT1': ('2001 AT1', None, None), 
        '(1714) Sy': (None, 1714, 'Sy'),
        '1714 SY': ('1714 SY', None, None), # not real, just for testing
        '2014 MU69': ('2014 MU69', None, None),
        '(228195) 6675 P-L': ('6675 P-L', 228195, None),
        '4015 Wilson-Harrington (1979 VA)': ('1979 VA', 4015,
                                             'Wilson-Harrington'),
        'J95X00A': ('1995 XA', None, None),
        'K07Tf8A': ('2007 TA418', None, None),
        'G3693': (None, 163693, None)
    }

    for comet, des in comets.items():
        q = callhorizons.query(comet, smallbody=True)
        _ident = q.parse_comet()
        assert _ident[0] == des[0], 'Parsed {}: {} != {}'.format(comet,
                                                            _ident[0], des[0])
        assert _ident[1] == des[1], 'Parsed {}: {} != {}'.format(comet,
                                                            _ident[1], des[1])
        assert _ident[2] == des[2], 'Parsed {}: {} != {}'.format(comet,
                                                            _ident[2], des[2])

    for asteroid, des in asteroids.items():
        q = callhorizons.query(asteroid, smallbody=True)
        _ident = q.parse_asteroid()
        assert _ident[0] == des[0], 'Parsed {}: {} != {}'.format(asteroid,
                                                            _ident[0], des[0])
        assert _ident[1] == des[1], 'Parsed {}: {} != {}'.format(asteroid,
                                                            _ident[1], des[1])
        assert _ident[2] == des[2], 'Parsed {}: {} != {}'.format(asteroid,
                                                            _ident[2], des[2])

def test_comet():
    """Test CAP and orbit record numbers for a comet."""
    
    # test failure when multiple orbital solutions are available
    target = callhorizons.query('9P', cap=False)
    target.set_discreteepochs([2451544.500000])

    try:
        target.get_ephemerides('G37')
    except ValueError as e:
        assert 'Ambiguous target name' in str(e)
    else:
        raise

    # switch to current ephemeris, this should be successful
    target.cap = True
    target.get_ephemerides('G37')
    assert len(target) == 1

    # Test orbit record number, note that NAIF may change these at any time.
    target = callhorizons.query('900191')
    target.set_discreteepochs([2451544.500000])
    target.get_ephemerides('G37')
    assert len(target) == 1
    
if __name__ == "__main__":
    test_ephemerides()
    test_elements()
    test_pyephem()
    test_designations()
    test_comet()
