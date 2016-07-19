"""CALLHORIZONS - a Python 2.7 interface to access JPL HORIZONS
ephemerides and orbital elements.

This module provides a convenient python interface to the JPL
HORIZONS system by directly accessing and parsing the HORIZONS
website. Ephemerides can be obtained through get_ephemerides,
orbital elements through get_elements. Function 
export2pyephem provides an interface to the PyEphem module.

michael.mommert (at) nau.edu, latest version: v1.0, 2016-07-19.
This code is inspired by code created by Alex Hagen.

"""

import time
import numpy
import urllib2


class query():

    ### constructor

    def __init__(self, targetname, smallbody=True):
        """
        Initialize query to Horizons 

        Parameters
        ----------
        targetname         : str
           HORIZONS-readable target number, name, or designation
        smallbody          : boolean
           use ``smallbody=False`` if targetname is a planet or spacecraft (optional, default: True)
        

        Results
        -------
        None

        """

        self.targetname     = str(targetname)
        self.not_smallbody  = not smallbody
        self.start_epoch    = None
        self.stop_epoch     = None
        self.step_size      = None
        self.discreteepochs = None
        self.url            = None 
        self.data           = None
        
        return None


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
            return self.data.shape[0]
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
            print 'CALLHORIZONS ERROR: run get_ephemerides or get_elements ' + \
                  'first'
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
        >>> print ceres.get_ephemerides(568), 'epochs queried'

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
        quantities = '1,3,4,8,9,10,18,19,20,21,23,24,27,33,36'

        # encode objectname for use in URL
        objectname = urllib2.quote(self.targetname.encode("utf8"))

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

        # check if self.targetname is a designation
        # lower case + upper case + numbers = pot. case sensitive designation
        if self.not_smallbody:
            url += "&COMMAND='" + \
                   urllib2.quote(self.targetname.encode("utf8")) + "'"
        elif (not self.targetname.replace(' ', '').isalpha() and not
             self.targetname.isdigit() and not
             self.targetname.islower() and not
             self.targetname.isupper()):
            url += "&COMMAND='DES=" + \
                   urllib2.quote(self.targetname.encode("utf8")) + "%3B'" 
        else:
            url += "&COMMAND='" + \
                   urllib2.quote(self.targetname.encode("utf8")) + "%3B'" 

        if self.discreteepochs is not None: 
            if len(self.discreteepochs) > 15:
                print 'CALLHORIZONS WARNING: more than 15 discrete epochs ' +\
                    'provided; output may be truncated.'
            url += "&TLIST=" 
            for date in self.discreteepochs:
                url += "'" + str(date) + "'"
        elif (self.start_epoch is not None and self.stop_epoch is not None and 
              self.step_size is not None):
            url +=  "&START_TIME='" \
                    + urllib2.quote(self.start_epoch.encode("utf8")) + "'" \
                    + "&STOP_TIME='" \
                    + urllib2.quote(self.stop_epoch.encode("utf8")) + "'" \
                    + "&STEP_SIZE='" + str(self.step_size) + "'"
        else:
            print 'CALLHORIZONS ERROR: no epoch information given'
            return 0
            
        if airmass_lessthan < 99:
            url += "&AIRMASS='" + str(airmass_lessthan) + "'"

        if skip_daylight:
            url += "&SKIP_DAYLT='YES'"
        else:
            url += "&SKIP_DAYLT='NO'"

        self.url = url

        #print url

        ### call HORIZONS 
        while True:
            try:
                src = urllib2.urlopen(url).readlines()
                break
            except urllib2.URLError:
                time.sleep(1)
                # in case the HORIZONS website is blocked (due to another query)
                # wait 1 second and try again


        ### disseminate website source code
        # identify header line and extract data block (ephemerides data)
        # also extract targetname, absolute mag. (H), and slope parameter (G)
        headerline = []
        datablock = []
        in_datablock = False
        H, G = None, None 
        for idx,line in enumerate(src):
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
            if src[idx].find("rotational period in hours)")>-1:
                HGline = src[idx+2].split('=')
                if HGline[2].find('B-V') > -1 and HGline[1].find('n.a.') == -1:
                    H = float(HGline[1].rstrip('G'))
                    G = float(HGline[2].rstrip('B-V'))
            if ("Multiple major-bodies match string" in src[idx] or
               ("Matching small-bodies" in src[idx] and not
                "No matches found" in src[idx+1])):
                raise ValueError('Ambiguous target name; check URL: %s' %
                                 url)
            if ("Matching small-bodies" in src[idx] and
                "No matches found" in src[idx+1]):
                raise ValueError('Unknown target; check URL: %s' % url)


        ### field identification for each line in 
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

                if (item.find('Date__(UT)__HR:MN') > -1):
                    this_eph.append(line[idx].strip())
                    fieldnames.append('datetime')
                    datatypes.append(object)
                if (item.find('Date_________JDUT') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('datetime_jd')
                    datatypes.append(float)
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
                    this_eph.append(float(line[idx]))
                    fieldnames.append('RA')
                    datatypes.append(float)
                if (item.find('DEC_(ICRF/J2000.0)') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('DEC')
                    datatypes.append(float)
                if (item.find('dRA*cosD') > -1):
                    try:
                        this_eph.append(float(line[idx])/3600.)  # "/s
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('RA_rate')
                    datatypes.append(float)
                if (item.find('d(DEC)/dt') > -1):
                    try:
                        this_eph.append(float(line[idx])/3600.)  # "/s
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('DEC_rate')
                    datatypes.append(float)
                if (item.find('Azi_(a-app)') > -1):
                    try: # if AZ not given, e.g. for space telescopes
                        this_eph.append(float(line[idx]))
                        fieldnames.append('AZ')
                        datatypes.append(float)
                    except ValueError: 
                        pass
                if (item.find('Elev_(a-app)') > -1):
                    try: # if EL not given, e.g. for space telescopes
                        this_eph.append(float(line[idx]))
                        fieldnames.append('EL')
                        datatypes.append(float)
                    except ValueError:
                        pass
                if (item.find('a-mass') > -1):
                    try: # if airmass not given, e.g. for space telescopes
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('airmass')
                    datatypes.append(float)
                if (item.find('mag_ex') > -1):
                    try: # if mag_ex not given, e.g. for space telescopes
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('magextinct')
                    datatypes.append(float)
                if (item.find('APmag') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('V')
                    datatypes.append(float)
                if (item.find('Illu%') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('illumination')
                    datatypes.append(float)
                if (item.find('hEcl-Lon') > -1):
                    try:              
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('EclLon')
                    datatypes.append(float)
                if (item.find('hEcl-Lat') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('EclLat')
                    datatypes.append(float)
                if (item.find('  r') > -1) and \
                   (headerline[idx+1].find("rdot") > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('r')
                    datatypes.append(float)
                if (item.find('rdot') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('r_rate')
                    datatypes.append(float)
                if (item.find('delta') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('delta')
                    datatypes.append(float)
                if (item.find('deldot') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('delta_rate')
                    datatypes.append(float)
                if (item.find('1-way_LT') > -1):
                    try:
                        this_eph.append(float(line[idx])*60.) # seconds
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('lighttime')
                    datatypes.append(float)
                if (item.find('S-O-T') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('elong')
                    datatypes.append(float)
                # in the case of space telescopes, '/r     S-T-O' is used;
                # ground-based telescopes have both parameters in separate
                # columns
                if (item.find('/r    S-T-O') > -1):
                    this_eph.append({'/L':'leading', '/T':'trailing'}\
                                    [line[idx].split()[0]])
                    fieldnames.append('elongFlag')
                    datatypes.append(object)
                    try:
                        this_eph.append(float(line[idx].split()[1]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('alpha')
                    datatypes.append(float)
                elif (item.find('S-T-O') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('alpha')
                    datatypes.append(float)
                elif (item.find('/r') > -1):
                    this_eph.append({'/L':'leading', '/T':'trailing'}\
                                    [line[idx]])
                    fieldnames.append('elongFlag')
                    datatypes.append(object)
                if (item.find('PsAng') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('sunTargetPA')
                    datatypes.append(float)
                if (item.find('PsAMV') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('velocityPA')
                    datatypes.append(float)
                if (item.find('GlxLon') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('GlxLon')
                    datatypes.append(float)
                if (item.find('GlxLat') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('GlxLat')
                    datatypes.append(float)
                if (item.find('RA_3sigma') > -1):
                    try: 
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('RA_3sigma')
                    datatypes.append(float)
                if (item.find('DEC_3sigma') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('DEC_3sigma')
                    datatypes.append(float)
                # in the case of a comet, use total mag for V
                if (item.find('T-mag') > -1):
                    try:
                        this_eph.append(float(line[idx]))
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('V')
                    datatypes.append(float)
            # append target name
            this_eph.append(targetname)
            fieldnames.append('targetname')
            datatypes.append(object)
            # append H, G; if they exist 
            try:
                this_eph.append(H)
                fieldnames.append('H')
                datatypes.append(float)
                this_eph.append(G)
                fieldnames.append('G')
                datatypes.append(float)
            except UnboundLocalError:
                pass

            if len(this_eph) > 0:
                ephemerides.append(tuple(this_eph))

        if len(ephemerides) == 0:
            return 0

        # combine ephemerides with column names and data types into ndarray
        assert len(ephemerides[0]) == len(fieldnames) == len(datatypes)
        self.data = numpy.array(ephemerides, 
                               dtype=[(fieldnames[i], datatypes[i]) for i 
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
        >>> print ceres.get_elements(), 'epochs queried'

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
        objectname = urllib2.quote(self.targetname.encode("utf8"))

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
                   urllib2.quote(self.targetname.encode("utf8")) + "'"
        elif (not self.targetname.replace(' ', '').isalpha() and not
             self.targetname.isdigit() and not
             self.targetname.islower() and not
             self.targetname.isupper()):
            url += "&COMMAND='DES=" + str(objectname) + "%3B'" 
        else:
            url += "&COMMAND='" + str(objectname) + "%3B'" 


        if self.discreteepochs is not None: 
            if len(self.discreteepochs) > 15:
                print 'CALLHORIZONS WARNING: more than 15 discrete epochs ' +\
                    'provided; output may be truncated.'
            url += "&TLIST=" 
            for date in self.discreteepochs:
                url += "'" + str(date) + "'"
        elif (self.start_epoch is not None and self.stop_epoch is not None and 
              self.step_size is not None):
            url +=  "&START_TIME='" \
                    + urllib2.quote(self.start_epoch.encode("utf8")) + "'" \
                    + "&STOP_TIME='" \
                    + urllib2.quote(self.stop_epoch.encode("utf8")) + "'" \
                    + "&STEP_SIZE='" + str(self.step_size) + "'"
        else:
            print 'CALLHORIZONS ERROR: no epoch information given'
            return 0
        
        self.url = url


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
        # also extract targetname, abs. magnitude (H), and slope parameter (G)
        headerline = []
        datablock = []
        in_datablock = False
        for idx,line in enumerate(eph):
            if line.find('EC, QR, IN, OM,') > -1:
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
            if ("Multiple major-bodies match string" in eph[idx] or
               ("Matching small-bodies" in eph[idx] and not
                "No matches found" in eph[idx+1])):
                raise ValueError('Ambiguous target name; check URL: %s' %
                                 url)
            if ("Matching small-bodies" in eph[idx] and
                "No matches found" in eph[idx+1]):
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
                    this_el.append(float(line[idx]))
                    fieldnames.append('datetime_jd')
                    datatypes.append(float)
                if (item.find('EC') > -1):                           
                    this_el.append(float(line[idx]))
                    fieldnames.append('e')
                    datatypes.append(float)
                if (item.find('QR') > -1):                           
                    this_el.append(float(line[idx]))
                    fieldnames.append('p')
                    datatypes.append(float)
                if (item.find('A') > -1) and len(item.strip()) == 1:
                    this_el.append(float(line[idx]))
                    fieldnames.append('a')
                    datatypes.append(float)
                if (item.find('IN') > -1):                           
                    this_el.append(float(line[idx]))
                    fieldnames.append('incl')
                    datatypes.append(float)
                if (item.find('OM') > -1):                           
                    this_el.append(float(line[idx]))
                    fieldnames.append('node')
                    datatypes.append(float)
                if (item.find('W') > -1):                           
                    this_el.append(float(line[idx]))
                    fieldnames.append('argper')
                    datatypes.append(float)
                if (item.find('Tp') > -1):                           
                    this_el.append(float(line[idx]))
                    fieldnames.append('Tp')
                    datatypes.append(float)
                if (item.find('MA') > -1):                           
                    this_el.append(float(line[idx]))
                    fieldnames.append('meananomaly')
                    datatypes.append(float)
                if (item.find('TA') > -1):                           
                    this_el.append(float(line[idx]))
                    fieldnames.append('trueanomaly')
                    datatypes.append(float)
                if (item.find('PR') > -1):                           
                    this_el.append(float(line[idx])/(365.256)) # Earth years
                    fieldnames.append('period')
                    datatypes.append(float)
                if (item.find('AD') > -1):                           
                    this_el.append(float(line[idx]))
                    fieldnames.append('Q')
                    datatypes.append(float)
            this_el.append(targetname)
            fieldnames.append('targetname')
            datatypes.append(object)
            try:
                this_el.append(H)
                fieldnames.append('H')
                datatypes.append(float)
                this_el.append(G)
                fieldnames.append('G')
                datatypes.append(float)
            except UnboundLocalError:
                pass

            if len(this_el) > 0:
                elements.append(tuple(this_el))

        if len(elements) == 0:
            return 0
                
        # combine elements with column names and data types into ndarray
        assert len(elements[0]) == len(fieldnames) == len(datatypes)
        self.data = numpy.array(elements, 
                               dtype=[(fieldnames[i], datatypes[i]) for i 
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
        >>> print 'next rising: %s' % nau.next_rising(ceres_pyephem[0])
        >>> print 'next transit: %s' % nau.next_transit(ceres_pyephem[0])
        >>> print 'next setting: %s' % nau.next_setting(ceres_pyephem[0])

        """

        try:
            import ephem
        except ImportError:
            print "ERROR: cannot import module PyEphem"
            return None

        # obtain orbital elements
        self.get_elements(center)

        objects = []
        for el in self.data:
            n = 0.9856076686/numpy.sqrt(el['a']**3) # mean daily motion
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


