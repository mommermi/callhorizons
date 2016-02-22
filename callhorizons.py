""" CALLHORIZONS - a python interface to JPL HORIZONS ephemerides and
    orbital elements

    This module provides a convenient python interface to the JPL
    HORIZONS system by directly accessing and parsing the http
    website. Ephemerides can be obtained through get_ephemerides,
    orbital elements through get_orbitalelements. Function 
    export2pyephem provides an interface to the PyEphem module.

    michael.mommert@nau.edu, 2016-01-06 (latest version: 2016-01-13)
    This code is inspired by code created by Alex Hagen.

"""

import math
import time
import urllib2

def what_is(key):
    """provides information on dictionary keys used in this module and
       how they are implemented
    """
    try:
        return { 'datetime': 'YYYY-MM-DD HH-MM in UT [string]',
                 'datetime_jd': 'Julian date [float]', 
                 'RA': 'right ascension (deg, J2000.0) [float]',
                 'DEC': 'declination (deg, J2000.0) [float]',
                 'RArate': 'RA rate (arcsec/sec, accounting for cos DEC) [float]', 
                 'DECrate': 'DEC rate (arcsec/sec) [float]',
                 'AZ': 'azimuth measured East (90) of North (0) (deg) [float]',
                 'EL': 'elevation (deg) [float]',
                 'airmass': 'optical airmass [string]',
                 'magextinct': 'V-mag extinction due to airmass (mag) [string]',
                 'V': 'V magnitude (total mag for comets) [float]',
                 'illumination': 'fraction of illuminated disk [float]',
                 'EclLon': 'heliocentr. ecliptic longitude (deg, J2000.0) [float]',
                 'EclLat': 'heliocentr. ecliptic latitude (deg, J2000.0) [float]',
                 'r': 'heliocentric distance (au) [float]',
                 'delta': 'distance from the observer (au) [float]',
                 'lighttime': 'one-way light time (sec) [float]',
                 'elong': 'solar elongation (deg) [float]', 
                 'elongFlag': 'apparent position relative to the Sun [string]',
                 'alpha': 'solar phase angle (deg) [float]',
                 'sunTargetPA': 'pos. angle of Sun->target vector (deg, EoN) [float]',
                 'velocityPA': 'position angle of velocity vector (deg, EoN) [float]',
                 'GlxLon': 'galactic longitude (deg) [float]',
                 'GlxLat': 'galactic latitude (deg) [float]',
                 'RA_3sigma': '3sigma pos. uncertainty in RA (arcsec) [float]',
                 'DEC_3sigma': '3sigma pos. uncertainty in DEC (arcsec) [float]',
                 'targetname': 'official number, name, designation [string]',
                 'H': 'absolute magnitude in V band (mag) [float]',
                 'G': 'photometric slope parameter [float]',
                 'e': 'eccentricity [float]',
                 'p': 'periapsis distance (au) [float]',
                 'a': 'semi-major axis (au) [float]',
                 'incl': 'inclination (deg) [float]',
                 'node': 'longitude of Asc. Node (deg) [float]',
                 'argper': 'argument of perifocus (deg) [float]',
                 'Tp': 'time of periapsis (Julian date) [float]',
                 'meananomaly': 'mean anomaly (deg) [float]',
                 'trueanomaly': 'true anomaly (deg) [float]',
                 'period': 'orbital period (Earth yr) [float]',
                 'Q': 'apoapsis distance (au) [float]'
             }[key]
    except KeyError:
        return "don't know key '%s'"% key
    

def get_ephemerides(objectname, observatory_code, 
                    start_time='', stop_time='', step_size='',
                    discretetimes=[], 
                    airmass_lessthan=99, 
                    solar_elongation=[0,180], 
                    skip_daylight=False):

    """call HORIZONS website to obtain ephemerides 

       Input: - objectname (target number, name, designation)
              - observatory_code (MPC observatory code)
              - start_time, stop_time (YYYY-MM-DD HH-MM UT) and
                step_size (e.g., 10m, 5h, 3d) or
              - discretetimes (array of max 15 julian dates)
              - airmass_lessthan (max airmass)
              - solar_elongation (permissible range in deg)
              - skip_daylight (True/False) 
       Output:  array of dictionaries with individual ephemerides
                for each time step
    """

    # queried fields (see HORIZONS website for details)
    # if fields are added here, also update the field identification below
    quantities = '1,3,4,8,9,10,18,19,20,21,23,24,27,33,36'

    # encode objectname for use in URL
    objectname = urllib2.quote(objectname.encode("utf8"))

    ### construct URL for HORIZONS query
    url = "http://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=l" \
          + "&TABLE_TYPE='OBSERVER'" \
          + "&QUANTITIES='" + str(quantities) + "'" \
          + "&CSV_FORMAT='YES'" \
          + "&ANG_FORMAT='DEG'" \
          + "&CAL_FORMAT='BOTH'" \
          + "&SOLAR_ELONG='" + str(solar_elongation[0]) + "," \
          + str(solar_elongation[1]) + "'" \
          + "&COMMAND='" + str(objectname) + "%3B'" \
          + "&CENTER='"+str(observatory_code)+"'"

    if len(discretetimes) > 0: 
        if len(discretetimes) > 15:
            print 'CALLHORIZONS WARNING: more than 15 discrete times provided;'
            print 'output may be truncated.'
        url = url + "&TLIST=" 
        for date in discretetimes:
            url = url + "'" + str(date) + "'"

    elif len(start_time) > 0 and len(stop_time) > 0 and len(step_size) > 0:
        url = url + "&START_TIME='" + str(start_time) + "'" \
              + "&STOP_TIME='" + str(stop_time) + "'" \
              + "&STEP_SIZE='" + str(step_size) + "'"

    if airmass_lessthan < 99:
        url = url + "&AIRMASS='" + str(airmass_lessthan) + "'"

    if skip_daylight:
        url = url + "&SKIP_DAYLT='YES'"
    else:
        url = url + "&SKIP_DAYLT='NO'"

    print url

    ### call HORIZONS 
    while True:
        try:
            eph = urllib2.urlopen(url).readlines()
            break
        except urllib2.URLError:
            time.sleep(1)
            # in case the HORIZONS website is blocked (due to another query)
            # wait 1 second and try again

    ### disseminate website source code
    # identify header line and extract data block (ephemerides data)
    # also extract targetname, absolute magnitude (H), and slope parameter (G)
    headerline = []
    datablock = []
    in_datablock = False
    for idx,line in enumerate(eph):
        if line.find('Date__(UT)__HR:MN') > -1:
            headerline = line.split(',')
        if line.find("$$EOE\n") > -1:
            in_datablock = False
        if in_datablock:
            datablock.append(line)
        if line.find("$$SOE\n") > -1:
            in_datablock = True
        if line.find("Target body name") > -1:
            targetname = line[18:50].strip()
        if eph[idx].find("rotational period in hours)")>-1:
            HGline = eph[idx+2].split('=')
            if HGline[2].find('B-V') > -1 and HGline[1].find('n.a.') == -1:
                H = float(HGline[1].rstrip('G'))
                G = float(HGline[2].rstrip('B-V'))

    ### field identification for each line in 
    ephemerides = []
    for line in datablock:
        line = line.split(',')
        information = {}

        # create a dictionary for each date (each line)
        for idx,item in enumerate(headerline):
            # ignore line that don't hold any data
            if len(line) < len(quantities.split(',')):
                continue

            if (item.find('Date__(UT)__HR:MN') > -1):
                information['datetime'] = line[idx]
            if (item.find('Date_________JDUT') > -1):
                information['datetime_jd'] = float(line[idx])
            if (item.find('R.A._(ICRF/J2000.0)') > -1):
                information['RA'] = float(line[idx])
            if (item.find('DEC_(ICRF/J2000.0)') > -1):
                information['DEC'] = float(line[idx])
            if (item.find('dRA*cosD') > -1):
                information['RArate'] = float(line[idx])/3600.
                # arcsec per second
            if (item.find('d(DEC)/dt') > -1):
                information['DECrate'] = float(line[idx])/3600.
                # arcsec per second
            if (item.find('Azi_(a-app)') > -1):
                try: # AZ not given, e.g. for space telescopes
                    information['AZ'] = float(line[idx])
                except ValueError: 
                    pass
            if (item.find('Elev_(a-app)') > -1):
                try: # EL not given, e.g. for space telescopes                
                    information['EL'] = float(line[idx])
                except ValueError:
                    pass
            if (item.find('a-mass') > -1):
                information['airmass'] = line[idx]
            if (item.find('mag_ex') > -1):
                information['magextinct'] = line[idx]
            if (item.find('APmag') > -1):
                information['V'] = float(line[idx])
            if (item.find('Illu%') > -1):
                information['illumination'] = float(line[idx])            
            if (item.find('hEcl-Lon') > -1):
                information['EclLon'] = float(line[idx]) 
            if (item.find('hEcl-Lat') > -1):
                information['EclLat'] = float(line[idx]) 
            if (item.find('  r') > -1) and \
               (headerline[idx+1].find("rdot") > -1):
                information['r'] = float(line[idx])
            if (item.find('delta') > -1):
                information['delta'] = float(line[idx])
            if (item.find('1-way_LT') > -1):
                information['lighttime'] = float(line[idx])*60.
            if (item.find('S-O-T') > -1):
                information['elong'] = float(line[idx])
            if (item.find('S-T-O') > -1):
                information['alpha'] = float(line[idx])
            if (item.find('/r') > -1):
                information['elongFlag'] = {'/L':'leading', '/T':'trailing'}\
                                           [line[idx]]
            if (item.find('PsAng') > -1):
                information['sunTargetPA'] = line[idx]
            if (item.find('PsAMV') > -1):
                information['velocityPA'] = float(line[idx])
            if (item.find('GlxLon') > -1):
                information['GlxLon'] = float(line[idx])
            if (item.find('GlxLat') > -1):
                information['GlxLat'] = float(line[idx])
            if (item.find('RA_3sigma') > -1):
                if line[idx].find('n.a.') > -1:
                    information['RA_3sigma'] = -1
                else:
                    information['RA_3sigma'] = float(line[idx])
            if (item.find('DEC_3sigma') > -1):
                if line[idx].find('n.a.') > -1:
                    information['DEC_3sigma'] = -1
                else:
                    information['DEC_3sigma'] = float(line[idx])
            if (item.find('T-mag') > -1):
                information['V'] = float(line[idx])
            information['targetname'] = targetname
            # H, G may not exist (e.g., in the case of comets)
            try:
                information['H'] = H
                information['G'] = G
            except UnboundLocalError:
                pass

        if len(information.keys()) > 0:
            ephemerides.append(information)

    return ephemerides




def get_orbitalelements(objectname,  
                        start_time='', stop_time='', step_size='',
                        discretetimes=[], 
                        center='500@10'):
    """call HORIZONS website to obtain orbital elements for different epochs

       Input: - objectname (target number, name, designation)
              - start_time, stop_time (YYYY-MM-DD HH-MM UT) and
                step_size (e.g., 10m, 5h, 3d) or
              - discretetimes (array of max 15 julian dates)
              - center_code (if other than the Sun's center)
       Output:  array of dictionaries with individual orbital
                elements for each time step
    """

    # encode objectname for use in URL
    objectname = urllib2.quote(objectname.encode("utf8"))

    ### call Horizons website and extract data
    url = "http://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=l" \
          + "&TABLE_TYPE='ELEMENTS'" \
          + "&CSV_FORMAT='YES'" \
          + "&COMMAND='" + str(objectname) + "%3B'" \
          + "&CENTER='" + str(center) + "'" \
          + "&OUT_UNITS='AU-D'" \
          + "&REF_PLANE='ECLIPTIC'" \
          + "REF_SYSTEM='J2000'" \
          + "&TP_TYPE='ABSOLUTE'" \
          + "&ELEM_LABELS='YES'" \
          + "CSV_FORMAT='YES'" \
          + "&OBJ_DATA='YES'"

    if len(discretetimes) > 0: 
        if len(discretetimes) > 15:
            print 'CALLHORIZONS WARNING: more than 15 discrete times provided;'
            print 'output may be truncated.'
        url = url + "&TLIST=" 
        for date in discretetimes:
            url = url + "'" + str(date) + "'"

    elif len(start_time) > 0 and len(stop_time) > 0 and len(step_size) > 0:
        url = url + "&START_TIME='" + str(start_time) + "'" \
              + "&STOP_TIME='" + str(stop_time) + "'" \
              + "&STEP_SIZE='" + str(step_size) + "'"

    #print url

    ### call HORIZONS 
    while True:
        try:
            eph = urllib2.urlopen(url).readlines()
            break
        except urllib2.URLError:
            time.sleep(1)
            # in case the HORIZONS website is blocked (due to another query)
            # wait 1 second and try again

    ### disseminate website source code
    # identify header line and extract data block (ephemerides data)
    # also extract targetname, absolute magnitude (H), and slope parameter (G)
    headerline = []
    datablock = []
    in_datablock = False
    for idx,line in enumerate(eph):
        if line.find('JDCT ,') > -1:
            headerline = line.split(',')
        if line.find("$$EOE\n") > -1:
            in_datablock = False
        if in_datablock:
            datablock.append(line)
        if line.find("$$SOE\n") > -1:
            in_datablock = True
        if line.find("Target body name") > -1:
            targetname = line[18:50].strip()
        if eph[idx].find("rotational period in hours)")>-1:
            HGline = eph[idx+2].split('=')
            if HGline[2].find('B-V') > -1 and HGline[1].find('n.a.') == -1:
                H = float(HGline[1].rstrip('G'))
                G = float(HGline[2].rstrip('B-V'))

    ### field identification for each line in 
    elements = []
    for line in datablock:
        line = line.split(',')
        information = {}

        # create a dictionary for each date (each line)
        for idx,item in enumerate(headerline):
            if (item.find('JDCT') > -1):                           
                information['datetime_jd'] = float(line[idx])
            if (item.find('EC') > -1):                           
                information['e'] = float(line[idx])
            if (item.find('QR') > -1):                           
                information['p'] = float(line[idx])
            if (item.find('A') > -1) and len(item.strip()) == 1:
                information['a'] = float(line[idx])
            if (item.find('IN') > -1):                           
                information['incl'] = float(line[idx])
            if (item.find('OM') > -1):                           
                information['node'] = float(line[idx])
            if (item.find('W') > -1):                           
                information['argper'] = float(line[idx])
            if (item.find('Tp') > -1):                           
                information['Tp'] = float(line[idx])
            if (item.find('MA') > -1):                           
                information['meananomaly'] = float(line[idx])
            if (item.find('TA') > -1):                           
                information['trueanomaly'] = float(line[idx])
            if (item.find('PR') > -1):                           
                information['period'] = float(line[idx])/(365.256)
                # period in Earth years
            if (item.find('AD') > -1):                           
                information['Q'] = float(line[idx])
            information['targetname'] = targetname
            information['H'] = H
            information['G'] = G

        if len(information.keys()) > 0:
            elements.append(information)

    return elements


def export2pyephem(objectname,  
                   start_time='', stop_time='', step_size='',
                   discretetimes=[], 
                   center='500@10',
                   equinox=2000.):
    """obtain orbital elements and export them into pyephem objects 
       (note: this function requires PyEphem to be installed)
    
       Input: - objectname (target number, name, designation)
              - start_time, stop_time (YYYY-MM-DD HH-MM UT) and
                step_size (e.g., 10m, 5h, 3d) or
              - discretetimes (array of max 15 julian dates)
              - center_code (if other than the Sun's center)
       Output:  array of pyephem objects for each time step

    """

    try:
        import ephem
    except ImportError:
        print "ERROR: cannot import module PyEphem"
        return None

    # obtain orbital elements
    elements = get_orbitalelements(objectname, start_time, stop_time,
                                   step_size, discretetimes, center)

    objects = []
    for el in elements:
        n = 0.9856076686/math.sqrt(el['a']**3) # mean daily motion
        epoch_djd = el['datetime_jd']-2415020.0  # Dublin Julian date
        epoch = ephem.date(epoch_djd)
        epoch_str = "%d/%f/%d" %(epoch.triple()[1], epoch.triple()[2], 
                                 epoch.triple()[0])

        # export to PyEphem
        objects.append(ephem.readdb("%s,e,%f,%f,%f,%f,%f,%f,%f,%s,%i,%f,%f" %
                                    (el['targetname'], el['incl'], el['node'],
                                     el['argper'], el['a'], n, el['e'],
                                     el['meananomaly'], epoch_str, equinox,
                                    el['H'], el['G'])))
    
    return objects




##### Example Code (just uncomment some of the following lines)

### use the what_is function to learn about the result parameters
# what_is('RA')
# what_is('Tp')


### call get_ephemerides using discrete times and a time range
# ephemerides = get_ephemerides('433', '568',
#                               discretetimes=[2457392.500000,
#                                              2457393.500000], 
#                               airmass_lessthan=5,
#                               skip_daylight=False)
# ephemerides = get_ephemerides('433', '568', start_time='2015-10-05',
#                               stop_time='2015-12-05', step_size='1d')

### print V magnitude, phase angle, heliocentric distance, and distance
### from the observer for each point in time
# for eph in ephemerides:
#   print eph['V'], eph['alpha'], eph['r'], eph['delta']



### call get_orbitalelements using discrete times and a time range
# elements = get_orbitalelements('433', discretetimes=[2457392.500000,
#                                                      2457393.500000])
# elements = get_orbitalelements('433', start_time='2015-10-05',
#                                stop_time='2015-12-05', step_size='1d')

### print all orbital elements for each point in time
# for el in elements:
#   for key in sorted(el.keys()):
#     print '%s=%s, ' % (key, str(el[key])),
#   print ''


### export orbital elements for 433 Eros to PyEphem and use it to
### determine rise, transit, and set times
# eros = export2pyephem('433', start_time='2015-10-05', stop_time='2015-12-05', 
#                       step_size='1d')

# # PyEphem code (see http://rhodesmill.org/pyephem/quick.html)
# import ephem
# nau = ephem.Observer() # setup observer site
# nau.lon = -111.653152/180.*math.pi
# nau.lat = 35.184108/180.*math.pi
# nau.elevation = 2100 # m
# nau.date = '2015/10/5 01:23' # UT 
# print ('next rise: %s\n' % nau.next_rising(eros[0])), \
#     ('next transit: %s\n' % nau.next_transit(eros[0])), \
#     ('next setting: %s' % nau.next_setting(eros[0]))


