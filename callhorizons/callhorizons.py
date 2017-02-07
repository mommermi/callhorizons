"""CALLHORIZONS - a Python interface to access JPL HORIZONS
ephemerides and orbital elements.

This module provides a convenient python interface to the JPL
HORIZONS system by directly accessing and parsing the HORIZONS
website. Ephemerides can be obtained through get_ephemerides,
orbital elements through get_elements. Function 
export2pyephem provides an interface to the PyEphem module.

michael.mommert (at) nau.edu, latest version: v1.0.1, 2016-07-19.
This code is inspired by code created by Alex Hagen.


v1.0.3: ObsEclLon and ObsEclLat added to get_ephemerides
v1.0.2: Python 3.5 compatibility implemented
v1.0.1: get_ephemerides fixed
v1.0:   bugfixes completed, planets/satellites accessible, too
v0.9:   first release


"""

from __future__ import (print_function, unicode_literals)


import time
import numpy as np
try:
    # Python 3
    import urllib.request as urllib
except ImportError:
    # Python 2
    import urllib2 as urllib




class query():

    ### constructor

    def __init__(self, targetname, smallbody=True, cap=True):
        """
        Initialize query to Horizons 

        Parameters
        ----------
        targetname         : str
           HORIZONS-readable target number, name, or designation
        smallbody          : boolean
           use ``smallbody=False`` if targetname is a planet or spacecraft (optional, default: True)
        cal                : boolean
           set to `True` to return the current apparition for comet targets.
        

        Results
        -------
        None

        """

        self.targetname     = str(targetname)
        self.not_smallbody  = not smallbody
        self.cap            = cap
        self.start_epoch    = None
        self.stop_epoch     = None
        self.step_size      = None
        self.discreteepochs = None
        self.url            = None 
        self.data           = None
        
        return None

    ### small body designation parsing

    def parse_comet(self):
        """Parse `targetname` as if it were a comet.

        Returns
        -------
        des : string or None
          The designation of the comet or `None` if `targetname` does
          not appear to be a comet name.  Note that comets starting
          with 'X/' are allowed, but this designation indicates a
          comet without an orbit, so `query()` should fail.

        Examples
        --------
        targetname                      des
        1P/Halley                       1P
        3D/Biela                        3D
        9P/Tempel 1                     9P
        73P/Schwassmann Wachmann 3 C    73P         # Note the missing "C"!
        73P-C/Schwassmann Wachmann 3 C  73P-C
        73P-BB                          73P-BB
        322P                            322P
        X/1106 C1                       X/1106 C1
        P/1994 N2 (McNaught-Hartley)    P/1994 N2
        P/2001 YX127 (LINEAR)           P/2001 YX127
        C/-146 P1                       C/-146 P1  
        C/2001 A2-A (LINEAR)            C/2001 A2-A
        C/2013 US10                     C/2013 US10
        C/2015 V2 (Johnson)             C/2015 V2

        """

        import re

        pat = ('^(([1-9]{1}[0-9]*[PD](-[A-Z]{1,2})?)'
               '|([CPX]/-?[0-9]{1,4} [A-Z]{1,2}[1-9][0-9]{0,2}(-[A-Z]{1,2})?))')

        m = re.findall(pat, self.targetname.strip())
        if len(m) == 0:
            return None
        else:
            return m[0][0]

    def parse_asteroid(self):
        """Parse `targetname` as if it were a asteroid.

        Returns
        -------
        des : string or None
          The designation of the asteroid or `None` if `targetname` does
          not appear to be an asteroid name.

        Examples
        --------
        targetname        des
        1                 1
        (2) Pallas        2
        (2001) Einstein   2001
        2001 AT1          2001 AT1
        (1714) Sy         1714
        1714 SY           1714 SY    # Note the near-confusion with (1714)
        2014 MU69         2014 MU69
        2017 AA           2017 AA

        """

        import re

        pat = ('^(([1-9][0-9]*( [A-Z]{1,2}([1-9][0-9]{0,2})?)?)'
               '|(\(([1-9][0-9]*)\)))')

        m = re.findall(pat, self.targetname.strip())
        if len(m) == 0:
            return None
        else:
            if len(m[0][5]) > 0:
                return m[0][5]
            else:
                return m[0][0]

    def isorbit_record(self):
        """`True` if `targetname` appears to be a comet orbit record number.

        NAIF record numbers are 6 digits, begin with a '9' and can
        change at any time.

        """
        
        import re
        test = re.match('^9[0-9]{5}$', self.targetname.strip()) is not None
        return test
            
    def iscomet(self):
        """`True` if `targetname` appears to be a comet."""
        return self.parse_comet() is not None

    def isasteroid(self):
        """`True` if `targetname` appears to be an asteroid."""
        return self.parse_asteroid() is not None

    ### set epochs

    def set_epochrange(self, start_epoch, stop_epoch, step_size):

        """Set a range of epochs, all times are UT

        Parameters
        ----------
        start_epoch        :    str
           start epoch of the format 'YYYY-MM-DD [HH-MM-SS]'
        stop_epoch         :    str
           final epoch of the format 'YYYY-MM-DD [HH-MM-SS]' 
        step_size          :    str
           epoch step size, e.g., '1d' for 1 day, '10m' for 10 minutes...

        Returns
        -------
        None
        
        Examples
        --------
        >>> import callhorizons
        >>> ceres = callhorizons.query('Ceres')
        >>> ceres.set_epochrange('2016-02-26', '2016-10-25', '1d')

        Note that dates are mandatory; if no time is given, midnight is assumed.
        """
        self.start_epoch = start_epoch
        self.stop_epoch  = stop_epoch
        self.step_size   = step_size

        return None


    def set_discreteepochs(self, discreteepochs):
        """Set a list of discrete epochs, epochs have to be given as Julian
        Dates

        Parameters
        ----------
        discreteepochs    : list
           list of floats or strings, maximum length: 15

        Returns
        -------
        None
        
        Examples
        --------
        >>> import callhorizons
        >>> ceres = callhorizons.query('Ceres')
        >>> ceres.set_discreteepochs([2457446.177083, 2457446.182343])
        
        If more than 15 epochs are provided, the list will be cropped to 15 epochs.
        """
        if type(discreteepochs) is not list:
            discreteepochs = [discreteepochs]

        self.discreteepochs = discreteepochs


    ### data access functions

    @property
    def fields(self):
        """returns list of available properties for all epochs"""
        try:
            return self.data.dtype.names
        except AttributeError:
            return []

    def __len__(self):
        """returns total number of epochs that have been queried"""
        try:
            # Cast to int because a long is returned from shape on Windows.
            return int(self.data.shape[0])
        except AttributeError:
            return 0
    
    @property
    def dates(self):
        """returns list of epochs that have been queried (format 'YYYY-MM-DD HH-MM-SS')"""
        try:
            return self.data['datetime']
        except:
            return []

    @property
    def query(self):
        """returns URL that has been used in calling HORIZONS"""
        try:
            return self.url
        except:
            return []


        
    @property
    def dates_jd(self):
        """returns list of epochs that have been queried (Julian Dates)"""
        try:
            return self.data['datetime_jd']
        except:
            return []

    def __repr__(self):
        """returns brief query information"""
        return "<callhorizons.query object: %s>" % self.targetname

    def __str__(self):
        """returns information on the current query as string"""
        output = "targetname: %s\n" % self.targetname
        if self.discreteepochs is not None:
            output += "discrete epochs: %s\n" % \
                      " ".join([str(epoch) for epoch in self.discreteepochs])
        if (self.start_epoch is not None and self.stop_epoch is not None and 
            self.step_size is not None):
            output += "epoch range from %s to %s in steps of %s\n" % \
                      (self.start_epoch, self.stop_epoch, self.step_size)
        output += "%d data sets queried with %d different fields" % \
                  (len(self), len(self.fields))
        return output


    def __getitem__(self, key):
        """provides access to query data

        Parameters
        ----------
        key          : str/int 
           epoch index or property key

        Returns
        -------
        query data according to key

        """

        # check if data exist
        if self.data is None or len(self.data) == 0:
            print ('CALLHORIZONS ERROR: run get_ephemerides or get_elements', 
                   'first')
            return None

        return self.data[key]



    ### call functions
        
    def get_ephemerides(self, observatory_code, 
                        airmass_lessthan=99, 
                        solar_elongation=(0,180), 
                        skip_daylight=False):
        """Call JPL HORIZONS website to obtain ephemerides based on the
        provided targetname, epochs, and observatory_code. For a list
        of valid observatory codes, refer to
        http://minorplanetcenter.net/iau/lists/ObsCodesF.html
        
        Parameters
        ----------
        observatory_code     : str/int
           observer's location code according to Minor Planet Center
        airmass_lessthan     : float
           maximum airmass (optional, default: 99)
        solar_elongation     : tuple
           permissible solar elongation range (optional, deg)
        skip_daylight        : boolean
           crop daylight epoch during query (optional)
        
        Results
        -------
        number of epochs queried
        
        Examples
        --------
        >>> ceres = callhorizons.query('Ceres')
        >>> ceres.set_epochrange('2016-02-23 00:00', '2016-02-24 00:00', '1h')
        >>> print (ceres.get_ephemerides(568), 'epochs queried')

        The queried properties and their definitions are:
           +------------------+-----------------------------------------------+
           | Property         | Definition                                    |
           +==================+===============================================+
           | targetname       | official number, name, designation [string]   |
           +------------------+-----------------------------------------------+
           | H                | absolute magnitude in V band (float, mag)     |
           +------------------+-----------------------------------------------+
           | G                | photometric slope parameter (float)           |
           +------------------+-----------------------------------------------+
           | datetime         | epoch date and time (str, YYYY-MM-DD HH:MM:SS)|
           +------------------+-----------------------------------------------+
           | datetime_jd      | epoch Julian Date (float)                     |
           +------------------+-----------------------------------------------+
           | solar_presence   | information on Sun's presence (str)           |
           +------------------+-----------------------------------------------+
           | lunar_presence   | information on Moon's presence (str)          |
           +------------------+-----------------------------------------------+
           | RA               | target RA (float, J2000.0)                    |
           +------------------+-----------------------------------------------+
           | DEC              | target DEC (float, J2000.0)                   |
           +------------------+-----------------------------------------------+
           | RA_rate          | target rate RA (float, arcsec/s)              |
           +------------------+-----------------------------------------------+
           | DEC_rate         | target RA (float, arcsec/s, includes cos(DEC))|
           +------------------+-----------------------------------------------+
           | AZ               | Azimuth meas East(90) of North(0) (float, deg)|
           +------------------+-----------------------------------------------+
           | EL               | Elevation (float, deg)                        |
           +------------------+-----------------------------------------------+
           | airmass          | target optical airmass (float)                |
           +------------------+-----------------------------------------------+
           | magextinct       | V-mag extinction due airmass (float, mag)     |
           +------------------+-----------------------------------------------+
           | V                | V magnitude (comets: total mag) (float, mag)  |
           +------------------+-----------------------------------------------+
           | illumination     | fraction of illuminated disk (float)          |
           +------------------+-----------------------------------------------+
           | EclLon           | heliocentr. ecl. long. (float, deg, J2000.0)  |
           +------------------+-----------------------------------------------+
           | EclLat           | heliocentr. ecl. lat. (float, deg, J2000.0)   |
           +------------------+-----------------------------------------------+
           | ObsEclLon        | obscentr. ecl. long. (float, deg, J2000.0)    |
           +------------------+-----------------------------------------------+
           | ObsEclLat        | obscentr. ecl. lat. (float, deg, J2000.0)     |
           +------------------+-----------------------------------------------+
           | r                | heliocentric distance (float, au)             |
           +------------------+-----------------------------------------------+
           | r_rate           | heliocentric radial rate  (float, km/s)       |
           +------------------+-----------------------------------------------+
           | delta            | distance from the observer (float, au)        |
           +------------------+-----------------------------------------------+
           | delta_rate       | obs-centric radial rate (float, km/s)         |
           +------------------+-----------------------------------------------+
           | lighttime        | one-way light time (float, s)                 |
           +------------------+-----------------------------------------------+
           | elong            | solar elongation (float, deg)                 |
           +------------------+-----------------------------------------------+
           | elongFlag        | app. position relative to Sun (str)           |
           +------------------+-----------------------------------------------+
           | alpha            | solar phase angle (float, deg)                |
           +------------------+-----------------------------------------------+
           | sunTargetPA      | PA of Sun->target vector (float, deg, EoN)    |
           +------------------+-----------------------------------------------+
           | velocityPA       | PA of velocity vector (float, deg, EoN)       |
           +------------------+-----------------------------------------------+
           | GlxLon           | galactic longitude (float, deg)               |
           +------------------+-----------------------------------------------+
           | GlxLat           | galactic latitude  (float, deg)               |
           +------------------+-----------------------------------------------+
           | RA_3sigma        | 3sigma pos. unc. in RA (float, arcsec)        |
           +------------------+-----------------------------------------------+
           | DEC_3sigma       | 3sigma pos. unc. in DEC (float, arcsec)       |
           +------------------+-----------------------------------------------+

        """
        
        # queried fields (see HORIZONS website for details)
        # if fields are added here, also update the field identification below
        quantities = '1,3,4,8,9,10,18,19,20,21,23,24,27,31,33,36'

        # encode objectname for use in URL
        objectname = urllib.quote(self.targetname.encode("utf8"))

        ### construct URL for HORIZONS query
        url = "http://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=l" \
              + "&TABLE_TYPE='OBSERVER'" \
              + "&QUANTITIES='" + str(quantities) + "'" \
              + "&CSV_FORMAT='YES'" \
              + "&ANG_FORMAT='DEG'" \
              + "&CAL_FORMAT='BOTH'" \
              + "&SOLAR_ELONG='" + str(solar_elongation[0]) + "," \
              + str(solar_elongation[1]) + "'" \
              + "&CENTER='"+str(observatory_code)+"'"

        if self.not_smallbody:
            url += "&COMMAND='" + \
                   urllib.quote(self.targetname.encode("utf8")) + "'"
        elif self.isorbit_record():
            # Comet orbit record. Do not use DES, CAP. This test must
            # occur before asteroid test.
            url += "&COMMAND='" + \
                   urllib.quote(self.targetname.encode("utf8")) + "%3B'"
        elif self.iscomet():
            # for comets, potentially append the current appararition
            # (CAP) parameter
            des = self.parse_comet()
            url += "&COMMAND='DES=" + \
                   urllib.quote(des.encode("utf8")) + "%3B" + \
                   ("CAP'" if self.cap else "'")
        elif self.isasteroid():
            # for asteroids, use 'DES="designation";'
            des = self.parse_asteroid()
            url += "&COMMAND='" + \
                   urllib.quote(des.encode("utf8")) + "%3B'"
        elif (not self.targetname.replace(' ', '').isalpha() and not
             self.targetname.isdigit() and not
             self.targetname.islower() and not
             self.targetname.isupper()):
            # lower case + upper case + numbers = pot. case sensitive designation
            url += "&COMMAND='DES=" + \
                   urllib.quote(self.targetname.encode("utf8")) + "%3B'" 
        else:
            url += "&COMMAND='" + \
                   urllib.quote(self.targetname.encode("utf8")) + "%3B'" 

        if self.discreteepochs is not None: 
            if len(self.discreteepochs) > 15:
                print ('CALLHORIZONS WARNING: more than 15 discrete epochs',
                       'provided; output may be truncated.')
            url += "&TLIST=" 
            for date in self.discreteepochs:
                url += "'" + str(date) + "'"
        elif (self.start_epoch is not None and self.stop_epoch is not None and 
              self.step_size is not None):
            url +=  "&START_TIME='" \
                    + urllib.quote(self.start_epoch.encode("utf8")) + "'" \
                    + "&STOP_TIME='" \
                    + urllib.quote(self.stop_epoch.encode("utf8")) + "'" \
                    + "&STEP_SIZE='" + str(self.step_size) + "'"
        else:
            raise IOError('no epoch information given')
            
        if airmass_lessthan < 99:
            url += "&AIRMASS='" + str(airmass_lessthan) + "'"

        if skip_daylight:
            url += "&SKIP_DAYLT='YES'"
        else:
            url += "&SKIP_DAYLT='NO'"

        self.url = url

        #print (url)

        ### call HORIZONS 
        i = 0  # count number of connection tries
        while True:
            try:
                src = urllib.urlopen(url).readlines()
                break
            except urllib.URLError:
                time.sleep(0.1)
                # in case the HORIZONS website is blocked (due to another query)
                # wait 0.1 second and try again
            i += 1
            if i > 50:
                return 0 # website could not be reached
                
        ### disseminate website source code
        # identify header line and extract data block (ephemerides data)
        # also extract targetname, absolute mag. (H), and slope parameter (G)
        headerline = []
        datablock = []
        in_datablock = False
        H, G = np.nan, np.nan
        for idx,line in enumerate(src):
            line = line.decode('UTF-8')

            if "Date__(UT)__HR:MN" in line:
                headerline = line.split(',')
            if "$$EOE\n" in line:
                in_datablock = False
            if in_datablock:
                datablock.append(line)
            if "$$SOE\n" in line:
                in_datablock = True
            if "Target body name" in line:
                targetname = line[18:50].strip()
            if ("rotational period in hours)" in
                src[idx].decode('UTF-8')):
                HGline = src[idx+2].decode('UTF-8').split('=')
                if 'B-V' in HGline[2]  and 'G' in HGline[1]:
                    H = float(HGline[1].rstrip('G'))
                    G = float(HGline[2].rstrip('B-V'))
            if ("Multiple major-bodies match string" in
                src[idx].decode('UTF-8') or
               ("Matching small-bodies" in src[idx].decode('UTF-8') and not
                "No matches found" in src[idx+1].decode('UTF-8'))):
                raise ValueError('Ambiguous target name; check URL: %s' %
                                 url)
            if ("Matching small-bodies" in src[idx].decode('UTF-8') and
                "No matches found" in src[idx+1].decode('UTF-8')):
                raise ValueError('Unknown target; check URL: %s' % url)


            
        ### field identification for each line
        ephemerides = []
        for line in datablock:
            line = line.split(',')
            
            # ignore line that don't hold any data
            if len(line) < len(quantities.split(',')):
                continue

            this_eph   = []
            fieldnames = []
            datatypes   = []

            # create a dictionary for each date (each line)
            for idx,item in enumerate(headerline):

                if ('Date__(UT)__HR:MN' in item):
                    this_eph.append(line[idx].strip())
                    fieldnames.append('datetime')
                    datatypes.append(object)
                if ('Date_________JDUT' in item):
                    this_eph.append(np.float64(line[idx]))
                    fieldnames.append('datetime_jd')
                    datatypes.append(np.float64)
                    # read out and convert solar presence
                    try:
                        this_eph.append({'*':'daylight', 'C':'civil twilight',
                                         'N':'nautical twilight',
                                         'A':'astronomical twilight',
                                         ' ':'dark',
                                         't':'transiting'}[line[idx+1]])
                    except KeyError:
                        this_eph.append('n.a.')
                    fieldnames.append('solar_presence')
                    datatypes.append(object)
                    # read out and convert lunar presence
                    try:
                        this_eph.append({'m':'moonlight',
                                         ' ':'dark'}[line[idx+2]])
                    except KeyError:
                        this_eph.append('n.a.')
                    fieldnames.append('lunar_presence')
                    datatypes.append(object)
                if (item.find('R.A._(ICRF/J2000.0)') > -1):
                    this_eph.append(np.float64(line[idx]))
                    fieldnames.append('RA')
                    datatypes.append(np.float64)
                if (item.find('DEC_(ICRF/J2000.0)') > -1):
                    this_eph.append(np.float64(line[idx]))
                    fieldnames.append('DEC')
                    datatypes.append(np.float64)
                if (item.find('dRA*cosD') > -1):
                    try:
                        this_eph.append(np.float64(line[idx])/3600.)  # "/s
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('RA_rate')
                    datatypes.append(np.float64)
                if (item.find('d(DEC)/dt') > -1):
                    try:
                        this_eph.append(np.float64(line[idx])/3600.)  # "/s
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('DEC_rate')
                    datatypes.append(np.float64)
                if (item.find('Azi_(a-app)') > -1):
                    try: # if AZ not given, e.g. for space telescopes
                        this_eph.append(np.float64(line[idx]))
                        fieldnames.append('AZ')
                        datatypes.append(np.float64)
                    except ValueError: 
                        pass
                if (item.find('Elev_(a-app)') > -1):
                    try: # if EL not given, e.g. for space telescopes
                        this_eph.append(np.float64(line[idx]))
                        fieldnames.append('EL')
                        datatypes.append(np.float64)
                    except ValueError:
                        pass
                if (item.find('a-mass') > -1):
                    try: # if airmass not given, e.g. for space telescopes
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('airmass')
                    datatypes.append(np.float64)
                if (item.find('mag_ex') > -1):
                    try: # if mag_ex not given, e.g. for space telescopes
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('magextinct')
                    datatypes.append(np.float64)
                if (item.find('APmag') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('V')
                    datatypes.append(np.float64)
                if (item.find('Illu%') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('illumination')
                    datatypes.append(np.float64)
                if (item.find('hEcl-Lon') > -1):
                    try:              
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('EclLon')
                    datatypes.append(np.float64)
                if (item.find('hEcl-Lat') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('EclLat')
                    datatypes.append(np.float64)
                if (item.find('ObsEcLon') > -1):
                    try:              
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('ObsEclLon')
                    datatypes.append(np.float64)
                if (item.find('ObsEcLat') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('ObsEclLat')
                    datatypes.append(np.float64)
                if (item.find('  r') > -1) and \
                   (headerline[idx+1].find("rdot") > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('r')
                    datatypes.append(np.float64)
                if (item.find('rdot') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('r_rate')
                    datatypes.append(np.float64)
                if (item.find('delta') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('delta')
                    datatypes.append(np.float64)
                if (item.find('deldot') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('delta_rate')
                    datatypes.append(np.float64)
                if (item.find('1-way_LT') > -1):
                    try:
                        this_eph.append(np.float64(line[idx])*60.) # seconds
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('lighttime')
                    datatypes.append(np.float64)
                if (item.find('S-O-T') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('elong')
                    datatypes.append(np.float64)
                # in the case of space telescopes, '/r     S-T-O' is used;
                # ground-based telescopes have both parameters in separate
                # columns
                if (item.find('/r    S-T-O') > -1):
                    this_eph.append({'/L':'leading', '/T':'trailing'}\
                                    [line[idx].split()[0]])
                    fieldnames.append('elongFlag')
                    datatypes.append(object)
                    try:
                        this_eph.append(np.float64(line[idx].split()[1]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('alpha')
                    datatypes.append(np.float64)
                elif (item.find('S-T-O') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('alpha')
                    datatypes.append(np.float64)
                elif (item.find('/r') > -1):
                    this_eph.append({'/L':'leading', '/T':'trailing'}\
                                    [line[idx]])
                    fieldnames.append('elongFlag')
                    datatypes.append(object)
                if (item.find('PsAng') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('sunTargetPA')
                    datatypes.append(np.float64)
                if (item.find('PsAMV') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('velocityPA')
                    datatypes.append(np.float64)
                if (item.find('GlxLon') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('GlxLon')
                    datatypes.append(np.float64)
                if (item.find('GlxLat') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('GlxLat')
                    datatypes.append(np.float64)
                if (item.find('RA_3sigma') > -1):
                    try: 
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('RA_3sigma')
                    datatypes.append(np.float64)
                if (item.find('DEC_3sigma') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('DEC_3sigma')
                    datatypes.append(np.float64)
                # in the case of a comet, use total mag for V
                if (item.find('T-mag') > -1):
                    try:
                        this_eph.append(np.float64(line[idx]))
                    except ValueError:
                        this_eph.append(np.nan)
                    fieldnames.append('V')
                    datatypes.append(np.float64)

            # append target name
            this_eph.append(targetname)
            fieldnames.append('targetname')
            datatypes.append(object)
            
            # append H
            this_eph.append(H)
            fieldnames.append('H')
            datatypes.append(np.float64)

            # append G
            this_eph.append(G)
            fieldnames.append('G')
            datatypes.append(np.float64)

            if len(this_eph) > 0:
                ephemerides.append(tuple(this_eph))

        if len(ephemerides) == 0:
            return 0

        # combine ephemerides with column names and data types into ndarray
        assert len(ephemerides[0]) == len(fieldnames) == len(datatypes)
        self.data = np.array(ephemerides, 
                               dtype=[(str(fieldnames[i]), datatypes[i]) for i 
                                      in range(len(fieldnames))])

        return len(self)




    def get_elements(self, center='500@10'):
        """Call JPL HORIZONS website to obtain orbital elements based on the
        provided targetname, epochs, and center code. For valid center
        codes, please refer to http://ssd.jpl.nasa.gov/horizons.cgi

        Parameters
        ----------
        center        :  str
           center body (default: 500@10 = Sun)

        Results
        -------
        number of epochs queried
        
        Examples
        --------
        >>> ceres = callhorizons.query('Ceres')
        >>> ceres.set_epochrange('2016-02-23 00:00', '2016-02-24 00:00', '1h')
        >>> print (ceres.get_elements(), 'epochs queried')

        The queried properties and their definitions are:
           +------------------+-----------------------------------------------+
           | Property         | Definition                                    |
           +==================+===============================================+
           | targetname       | official number, name, designation [string]   |
           +------------------+-----------------------------------------------+
           | H                | absolute magnitude in V band (float, mag)     |
           +------------------+-----------------------------------------------+
           | G                | photometric slope parameter (float)           |
           +------------------+-----------------------------------------------+
           | datetime_jd      | epoch Julian Date (float)                     |
           +------------------+-----------------------------------------------+
           | e                | eccentricity (float)                          |
           +------------------+-----------------------------------------------+
           | p                | periapsis distance (float, au)                |
           +------------------+-----------------------------------------------+
           | a                | semi-major axis (float, au)                   |
           +------------------+-----------------------------------------------+
           | incl             | inclination (float, deg)                      |
           +------------------+-----------------------------------------------+
           | node             | longitude of Asc. Node (float, deg)           |
           +------------------+-----------------------------------------------+
           | argper           | argument of the perifocus (float, deg)        |
           +------------------+-----------------------------------------------+
           | Tp               | time of periapsis (float, Julian Date)        |
           +------------------+-----------------------------------------------+
           | meananomaly      | mean anomaly (float, deg)                     |
           +------------------+-----------------------------------------------+
           | trueanomaly      | true anomaly (float, deg)                     |
           +------------------+-----------------------------------------------+
           | period           | orbital period (float, Earth yr)              |
           +------------------+-----------------------------------------------+
           | Q                | apoapsis distance (float, au)                 |
           +------------------+-----------------------------------------------+

        """

        # encode objectname for use in URL
        objectname = urllib.quote(self.targetname.encode("utf8"))

        ### call Horizons website and extract data
        url = "http://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=l" \
              + "&TABLE_TYPE='ELEMENTS'" \
              + "&CSV_FORMAT='YES'" \
              + "&CENTER='" + str(center) + "'" \
              + "&OUT_UNITS='AU-D'" \
              + "&REF_PLANE='ECLIPTIC'" \
              + "REF_SYSTEM='J2000'" \
              + "&TP_TYPE='ABSOLUTE'" \
              + "&ELEM_LABELS='YES'" \
              + "CSV_FORMAT='YES'" \
              + "&OBJ_DATA='YES'"

        # check if self.targetname is a designation
        # lower case + upper case + numbers = pot. case sensitive designation
        if self.not_smallbody:
            url += "&COMMAND='" + \
                   urllib.quote(self.targetname.encode("utf8")) + "'"
        elif (not self.targetname.replace(' ', '').isalpha() and not
             self.targetname.isdigit() and not
             self.targetname.islower() and not
             self.targetname.isupper()):
            url += "&COMMAND='DES=" + str(objectname) + "%3B'" 
        else:
            url += "&COMMAND='" + str(objectname) + "%3B'" 


        if self.discreteepochs is not None: 
            if len(self.discreteepochs) > 15:
                print ('CALLHORIZONS WARNING: more than 15 discrete epochs ',
                       'provided; output may be truncated.')
            url += "&TLIST=" 
            for date in self.discreteepochs:
                url += "'" + str(date) + "'"
        elif (self.start_epoch is not None and self.stop_epoch is not None and 
              self.step_size is not None):
            url +=  "&START_TIME='" \
                    + urllib.quote(self.start_epoch.encode("utf8")) + "'" \
                    + "&STOP_TIME='" \
                    + urllib.quote(self.stop_epoch.encode("utf8")) + "'" \
                    + "&STEP_SIZE='" + str(self.step_size) + "'"
        else:
            raise IOError('no epoch information given')
        
        self.url = url

        i = 0  # count number of connection tries
        while True:
            try:
                src = urllib.urlopen(url).readlines()
                break
            except urllib.URLError:
                time.sleep(0.1)
                # in case the HORIZONS website is blocked (due to another query)
                # wait 1 second and try again
            i += 1
            if i > 50:
                return 0 # website could not be reached

        ### disseminate website source code
        # identify header line and extract data block (elements data)
        # also extract targetname, abs. magnitude (H), and slope parameter (G)
        headerline = []
        datablock = []
        in_datablock = False
        H, G = np.nan, np.nan
        for idx,line in enumerate(src):
            line = line.decode('UTF-8')            

            if 'JDTDB,' in line:
                headerline = line.split(',')
            if "$$EOE\n" in line:
                in_datablock = False
            if in_datablock:
                datablock.append(line)
            if "$$SOE\n" in line:
                in_datablock = True
            if "Target body name" in line:
                targetname = line[18:50].strip()
            if "rotational period in hours)" in src[idx].decode('UTF-8'):
                HGline = src[idx+2].decode('UTF-8').split('=')
                if 'B-V' in HGline[2] and 'G' in HGline[1]:
                    H = float(HGline[1].rstrip('G'))
                    G = float(HGline[2].rstrip('B-V'))
            if ("Multiple major-bodies match string" in src[idx].decode('UTF-8') or
               ("Matching small-bodies" in src[idx].decode('UTF-8') and not
                "No matches found" in src[idx+1].decode('UTF-8'))):
                raise ValueError('Ambiguous target name; check URL: %s' %
                                 url)
            if ("Matching small-bodies" in src[idx].decode('UTF-8') and
                "No matches found" in src[idx+1].decode('UTF-8')):
                raise ValueError('Unknown target; check URL: %s' % url)


        ### field identification for each line in 
        elements = []
        for line in datablock:
            line = line.split(',')

            this_el   = []
            fieldnames = []
            datatypes   = []

            # create a dictionary for each date (each line)
            for idx,item in enumerate(headerline):
                if (item.find('JDTDB') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('datetime_jd')
                    datatypes.append(np.float64)
                if (item.find('EC') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('e')
                    datatypes.append(np.float64)
                if (item.find('QR') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('p')
                    datatypes.append(np.float64)
                if (item.find('A') > -1) and len(item.strip()) == 1:
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('a')
                    datatypes.append(np.float64)
                if (item.find('IN') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('incl')
                    datatypes.append(np.float64)
                if (item.find('OM') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('node')
                    datatypes.append(np.float64)
                if (item.find('W') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('argper')
                    datatypes.append(np.float64)
                if (item.find('Tp') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('Tp')
                    datatypes.append(np.float64)
                if (item.find('MA') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('meananomaly')
                    datatypes.append(np.float64)
                if (item.find('TA') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('trueanomaly')
                    datatypes.append(np.float64)
                if (item.find('PR') > -1):                           
                    this_el.append(np.float64(line[idx])/(365.256)) # Earth years
                    fieldnames.append('period')
                    datatypes.append(np.float64)
                if (item.find('AD') > -1):                           
                    this_el.append(np.float64(line[idx]))
                    fieldnames.append('Q')
                    datatypes.append(np.float64)

            # append targetname
            this_el.append(targetname)
            fieldnames.append('targetname')
            datatypes.append(object)

            # append H
            this_el.append(H)
            fieldnames.append('H')
            datatypes.append(np.float64)

            # append G
            this_el.append(G)
            fieldnames.append('G')
            datatypes.append(np.float64)

            if len(this_el) > 0:
                elements.append(tuple(this_el))

        if len(elements) == 0:
            return 0

        
        # combine elements with column names and data types into ndarray
        assert len(elements[0]) == len(fieldnames) == len(datatypes)
        self.data = np.array(elements, 
                               dtype=[(str(fieldnames[i]), datatypes[i]) for i 
                                      in range(len(fieldnames))])

        return len(self)



    def export2pyephem(self, center='500@10', equinox=2000.):
        """Call JPL HORIZONS website to obtain orbital elements based on the
        provided targetname, epochs, and center code and create a
        PyEphem (http://rhodesmill.org/pyephem/) object. This function
        requires PyEphem to be installed.
        
        Parameters
        ----------
        center        : str
           center body (default: 500@10 = Sun)
        equinox       : float
           equinox (default: 2000.0)

        Results
        -------
        list of PyEphem objects, one per epoch
        
        Examples
        --------
        >>> import callhorizons
        >>> import numpy
        >>> import ephem

        >>> ceres = callhorizons.query('Ceres')
        >>> ceres.set_epochrange('2016-02-23 00:00', '2016-02-24 00:00', '1h')
        >>> ceres_pyephem = ceres.export2pyephem()

        >>> nau = ephem.Observer() # setup observer site
        >>> nau.lon = -111.653152/180.*numpy.pi
        >>> nau.lat = 35.184108/180.*numpy.pi
        >>> nau.elevation = 2100 # m
        >>> nau.date = '2015/10/5 01:23' # UT 
        >>> print ('next rising: %s' % nau.next_rising(ceres_pyephem[0]))
        >>> print ('next transit: %s' % nau.next_transit(ceres_pyephem[0]))
        >>> print ('next setting: %s' % nau.next_setting(ceres_pyephem[0]))

        """

        try:
            import ephem
        except ImportError:
            raise ImportError('export2pyephem requires PyEphem to be installed')

        # obtain orbital elements
        self.get_elements(center)

        objects = []
        for el in self.data:
            n = 0.9856076686/np.sqrt(el['a']**3) # mean daily motion
            epoch_djd = el['datetime_jd']-2415020.0  # Dublin Julian date
            epoch = ephem.date(epoch_djd)
            epoch_str = "%d/%f/%d" %(epoch.triple()[1], epoch.triple()[2], 
                                     epoch.triple()[0])

            # export to PyEphem
            objects.append(ephem.readdb("%s,e,%f,%f,%f,%f,%f,%f,%f,%s,%i,%f,%f"%
                                    (el['targetname'], el['incl'], el['node'],
                                     el['argper'], el['a'], n, el['e'],
                                     el['meananomaly'], epoch_str, equinox,
                                    el['H'], el['G'])))
    
        return objects


