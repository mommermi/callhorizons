import callhorizons
import numpy as np

def test_ephemerides():
    """ check ephemerides output for one asteroid """

    asteroid_targetname = 'Ceres'
    target = callhorizons.query(asteroid_targetname)

    target.set_discreteepochs([2451544.500000])
    target.get_ephemerides(568)
    
    # compare all query results to values taken directly from Horizons
    # queried on Nov 6, 2016
    assert target['targetname'][0]           == u'1 Ceres'
    assert target['H'][0]                    == 3.34
    assert target['G'][0]                    == 0.12
    assert target['datetime'][0]             == u'2000-Jan-01 00:00:00.000'
    assert target['datetime_jd'][0]          == 2451544.5
    assert target['solar_presence'][0]       == 'daylight'
    assert target['lunar_presence'][0]       == 'dark'
    assert target['RA'][0]                   == 188.70188 
    assert target['DEC'][0]                  == 9.09786
    assert target['RA_rate'][0]              == 34.82656/3600    
    assert target['DEC_rate'][0]             == -2.82060/3600     
    assert target['AZ'][0]                   == 288.3275
    assert target['EL'][0]                   == -20.5230
    assert np.isnan(target['airmass'][0])
    assert np.isnan(target['magextinct'][0])
    assert target['V'][0]                    == 8.27
    assert target['illumination'][0]         == 96.171
    assert target['EclLon'][0]               == 161.3828       
    assert target['EclLat'][0]               == 10.4528        
    assert target['r'][0]                    == 2.551098889601
    assert target['r_rate'][0]               == 0.1744499       
    assert target['delta'][0]                == 2.26316614786857
    assert target['delta_rate'][0]           == -21.5499080   
    assert target['lighttime'][0]            == 18.822179*60
    assert target['elong'][0]                == 95.3997
    assert target['elongFlag'][0]            == u'leading'    
    assert target['alpha'][0]                == 22.5690
    assert target['sunTargetPA'][0]          == 292.552  
    assert target['velocityPA'][0]           == 296.849  
    assert target['GlxLon'][0]               == 289.861684     
    assert target['GlxLat'][0]               == 71.545053       
    assert target['RA_3sigma'][0]            == 0.058
    assert target['DEC_3sigma'][0]           == 0.05   


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
    assert target['datetime_jd'][0]  == 2451544.5
    assert target['e'][0]            == 0.003654784965339888
    assert target['p'][0]            == 2.811473523687107E-03
    assert target['a'][0]            == 2.821786546733507E-03
    assert target['incl'][0]         == 2.212609179741271E+00
    assert target['node'][0]         == 3.368501231726219E+02
    assert target['argper'][0]       == 6.218469675691234E+01
    assert target['Tp'][0]           == 2451545.103514090180
    assert target['meananomaly'][0]  == 2.373891296290639E+02
    assert target['trueanomaly'][0]  == 2.370372158041970E+02
    assert target['period'][0]       == 1.771988665071993/365.256
    assert target['Q'][0]            == 2.832099569779908E-03


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
    comets = {
        '1P/Halley': '1P',
        '3D/Biela': '3D',
        '9P/Tempel 1': '9P',
        '73P/Schwassmann Wachmann 3 C': '73P',  # Note the missing "C"!
        '73P-C/Schwassmann Wachmann 3 C': '73P-C',
        '73P-BB': '73P-BB',
        '322P': '322P',
        'X/1106 C1': 'X/1106 C1',
        'P/1994 N2 (McNaught-Hartley)': 'P/1994 N2',
        'P/2001 YX127 (LINEAR)': 'P/2001 YX127',
        'C/-146 P1': 'C/-146 P1' ,
        'C/2001 A2-A (LINEAR)': 'C/2001 A2-A',
        'C/2013 US10': 'C/2013 US10',
        'C/2015 V2 (Johnson)': 'C/2015 V2',
    }

    asteroids = {
        '1': '1',
        '(2) Pallas': '2',
        '(2001) Einstein': '2001',
        '2001 AT1': '2001 AT1',
        '(1714) Sy': '1714',
        '1714 SY': '1714 SY',
        '2014 MU69': '2014 MU69',
        '2017 AA': '2017 AA',
    }

    for comet, des in comets.items():
        q = callhorizons.query(comet, smallbody=True)
        _des = q.parse_comet() 
        assert _des == des, 'Parsed {}: {} != {}'.format(comet, _des, des)

    for asteroid, des in asteroids.items():
        q = callhorizons.query(asteroid, smallbody=True)
        _des = q.parse_asteroid()
        assert _des == des, 'Parsed {}: {} != {}'.format(asteroid, _des, des)
        
    
if __name__ == "__main__":
    test_ephemerides()
    test_elements()
    test_pyephem()
    test_designations()
