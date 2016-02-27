""" CALLHORIZONS - a python interface to JPL HORIZONS ephemerides and
    orbital elements

    This module provides a convenient python interface to the JPL
    HORIZONS system by directly accessing and parsing the HORIZONS
    website. Ephemerides can be obtained through get_ephemerides,
    orbital elements through get_elements. Function 
    export2pyephem provides an interface to the PyEphem module.

    michael.mommert@nau.edu, latest version: v0.9, 2016-02-27
    This code is inspired by code created by Alex Hagen.

"""

import time
import numpy
import urllib2


class query():

    ### constructor

    def __init__(self, targetname):
        """
        initialize call
        input: targetname (number, name, designation),
               [designation=True if targetname is a designation],
        """
        self.targetname    = targetname
        self.start_time    = None
        self.stop_time     = None
        self.step_size     = None
        self.discretetimes = None
        self.url           = None 
        self.data          = None


        return None


    ### set times

    def set_timerange(self, start_time, stop_time, step_size):
        """
        set a time range
        input: start_time (YYYY-MM-DD HH:MM), 
               stop_time  (YYYY-MM-DD HH:MM), 
               step_size  (#d/#h/#m...)
        """
        self.start_time = start_time
        self.stop_time  = stop_time
        self.step_size  = step_size

        return None


    def set_discretetimes(self, discretetimes):
        """
        set discrete times
        input: list of dates in JD
        """
        if type(discretetimes) is not list:
            discretetimes = [discretetimes]

        self.discretetimes = discretetimes


    ### data access functions

    @property
    def fields(self):
        """ 
        return available fields in self.data
        """
        try:
            return self.data.dtype.names
        except AttributeError:
            return []

    def __len__(self):
        """
        return number of dates queried
        """
        try:
            return self.data.shape[0]
        except AttributeError:
            return 0
    
    @property
    def dates(self):
        """
        return dates for available ephemerides/elements
        """
        try:
            return self.data['datetime']
        except:
            return []

    @property
    def dates_jd(self):
        """
        return Julian Dates for available ephemerides/elements
        """
        try:
            return self.data['datetime_jd']
        except:
            return []

    def __repr__(self):
        """
        provide brief query information
        """
        return "<callhorizons.query object: %s>" % self.targetname

    def __str__(self):
        """
        provide information on the current query as string
        """
        output = "targetname: %s\n" % self.targetname
        if self.discretetimes is not None:
            output += "discrete times: %s\n" % " ".join(self.discretetimes)
        if (self.start_time is not None and self.stop_time is not None and 
            self.step_size is not None):
            output += "time range from %s to %s in steps of %s\n" % \
                      (self.start_time, self.stop_time, self.step_size)
        output += "%d data sets queried with %d different fields" % \
                  (len(self), len(self.fields))
        return output


    def __getitem__(self, key):
        """ 
        access self.data for given key (date_idx, date or parameter)
        """

        # check if data exist
        if self.data is None or len(self.data) == 0:
            print 'CALLHORIZONS ERROR: run get_ephemerides or get_elements ' + \
                  'first'
            return None

        # decide what to return
        if type(key) == int:
            return self.data[key]
        elif 'datetime' in self.fields and key in self.data['datetime']:
            return self.data[self.data['datetime'] == key]
        elif 'datetime_jd' in self.fields and key in self.data['datetime_jd']:
            return self.data[self.data['datetime_jd'] == key]
        elif key in self.fields:
            return self.data[key]
        else:
            print 'CALLHORIZONS ERROR: not sure what to return ' +\
                  '(requested: %s)' % str(key)


    ### call functions
        
    def get_ephemerides(self, observatory_code, 
                        airmass_lessthan=99, 
                        solar_elongation=[0,180], 
                        skip_daylight=False):
        """
        call HORIZONS website to obtain ephemerides 
        input: observatory_code (MPC observatory code),
               [airmass_lessthan (max airmass)],
               [solar_elongation (permissible range in deg)],
               [skip_daylight (True/False)],
        output: number of ephemerides queried
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

        # lower case + upper case + numbers = pot. case sensitive designation
        if (not self.targetname.isalpha() and not
            self.targetname.isdigit() and not
            self.targetname.islower() and not
            self.targetname.isupper()):
            url += "&COMMAND='DES=" + str(objectname) + "%3B'" 
        else:
            url += "&COMMAND='" + str(objectname) + "%3B'" 

        if self.discretetimes is not None: 
            if len(self.discretetimes) > 15:
                print 'CALLHORIZONS WARNING: more than 15 discrete times ' +\
                    'provided; output may be truncated.'
            url += "&TLIST=" 
            for date in self.discretetimes:
                url += "'" + str(date) + "'"
        elif (self.start_time is not None and self.stop_time is not None and 
              self.step_size is not None):
            url +=  "&START_TIME='" \
                    + urllib2.quote(self.start_time.encode("utf8")) + "'" \
                    + "&STOP_TIME='" \
                    + urllib2.quote(self.stop_time.encode("utf8")) + "'" \
                    + "&STEP_SIZE='" + str(self.step_size) + "'"
        else:
            print 'CALLHORIZONS ERROR: no time information given'

        if airmass_lessthan < 99:
            url += "&AIRMASS='" + str(airmass_lessthan) + "'"

        if skip_daylight:
            url += "&SKIP_DAYLT='YES'"
        else:
            url += "&SKIP_DAYLT='NO'"

        self.url = url


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
                    this_eph.append({'*':'daylight', 'C':'civil twilight',
                                     'N':'nautical twilight',
                                     'A':'astronomical twilight',
                                     ' ':'dark'}[line[idx+1]])
                    fieldnames.append('solar_presence')
                    datatypes.append(object)
                    # read out and convert lunar presence
                    this_eph.append({'m':'moonlight', ' ':'dark'}[line[idx+2]])
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
                    fieldnames.append('RArate')
                    datatypes.append(float)
                if (item.find('d(DEC)/dt') > -1):
                    try:
                        this_eph.append(float(line[idx])/3600.)  # "/s
                    except ValueError:
                        this_eph.append(numpy.nan)
                    fieldnames.append('DECrate')
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
                    this_eph.append(float(line[idx]))
                    fieldnames.append('V')
                    datatypes.append(float)
                if (item.find('Illu%') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('illumination')
                    datatypes.append(float)
                if (item.find('hEcl-Lon') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('EclLon')
                    datatypes.append(float)
                if (item.find('hEcl-Lat') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('EclLat')
                    datatypes.append(float)
                if (item.find('  r') > -1) and \
                   (headerline[idx+1].find("rdot") > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('r')
                    datatypes.append(float)
                if (item.find('rdot') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('r_rate')
                    datatypes.append(float)
                if (item.find('delta') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('delta')
                    datatypes.append(float)
                if (item.find('deldot') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('delta_rate')
                    datatypes.append(float)
                if (item.find('1-way_LT') > -1):
                    this_eph.append(float(line[idx])*60.) # seconds
                    fieldnames.append('lighttime')
                    datatypes.append(float)
                if (item.find('S-O-T') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('elong')
                    datatypes.append(float)
                if (item.find('S-T-O') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('alpha')
                    datatypes.append(float)
                if (item.find('/r') > -1):
                    this_eph.append({'/L':'leading', '/T':'trailing'}\
                                    [line[idx]])
                    fieldnames.append('elongFlag')
                    datatypes.append(object)
                if (item.find('PsAng') > -1):
                    this_eph.append(line[idx])
                    fieldnames.append('sunTargetPA')
                    datatypes.append(float)
                if (item.find('PsAMV') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('velocityPA')
                    datatypes.append(float)
                if (item.find('GlxLon') > -1):
                    this_eph.append(float(line[idx]))
                    fieldnames.append('GlxLon')
                    datatypes.append(float)
                if (item.find('GlxLat') > -1):
                    this_eph.append(float(line[idx]))
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
                    this_eph.append(float(line[idx]))
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




    def get_elements(self, center='500@10', print_url=False):
        """
        call HORIZONS website to obtain orbital elements for different epochs
        input: [center_code (if other than the Sun's center)]
               [print_url (True/False)]
        output: number of element sets queried
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

        # lower case + upper case + numbers = pot. case sensitive designation
        if (not self.targetname.isalpha() and not
            self.targetname.isdigit() and not
            self.targetname.islower() and not
            self.targetname.isupper()):
            url += "&COMMAND='DES=" + str(objectname) + "%3B'" 
        else:
            url += "&COMMAND='" + str(objectname) + "%3B'" 


        if self.discretetimes is not None: 
            if len(self.discretetimes) > 15:
                print 'CALLHORIZONS WARNING: more than 15 discrete times ' +\
                    'provided; output may be truncated.'
            url += "&TLIST=" 
            for date in self.discretetimes:
                url += "'" + str(date) + "'"
        elif (self.start_time is not None and self.stop_time is not None and 
              self.step_size is not None):
            url +=  "&START_TIME='" \
                    + urllib2.quote(self.start_time.encode("utf8")) + "'" \
                    + "&STOP_TIME='" \
                    + urllib2.quote(self.stop_time.encode("utf8")) + "'" \
                    + "&STEP_SIZE='" + str(self.step_size) + "'"
        else:
            print 'CALLHORIZONS ERROR: no time information given'

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


        # combine elements with column names and data types into ndarray
        assert len(elements[0]) == len(fieldnames) == len(datatypes)
        self.data = numpy.array(elements, 
                               dtype=[(fieldnames[i], datatypes[i]) for i 
                                      in range(len(fieldnames))])

        return len(self)



    def export2pyephem(self, center='500@10', equinox=2000.):
        """
        obtain orbital elements and export them into pyephem objects 
        (note: this function requires PyEphem to be installed)
        
        input: [center_code (if other than the Sun's center)]
        output:  array of pyephem objects for each time step
        
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





    def whatis(self, key):
        """
        provides information on dictionary keys used in this module and
        how they are implemented
        """
        try:
            return {'datetime': 'YYYY-MM-DD HH-MM in UT [str]',
                    'datetime_jd': 'Julian date [float]', 
                    'solar_presence': 'information on Sun\'s presence [str]',
                    'lunar_presence': 'information on Moon\'s presence [str]',
                    'RA': 'right ascension (deg, J2000.0) [float]',
                    'DEC': 'declination (deg, J2000.0) [float]',
                    'RArate': 'RA rate (arcsec/sec, incl. cos DEC) [float]', 
                    'DECrate': 'DEC rate (arcsec/sec) [float]',
                    'AZ': 'azimuth meas. East (90) of North (0) (deg) [float]',
                    'EL': 'elevation (deg) [float]',
                    'airmass': 'optical airmass [float]',
                    'magextinct': 'V-mag extinction due airmass (mag) [float]',
                    'V': 'V magnitude (total mag for comets) [float]',
                    'illumination': 'fraction of illuminated disk [float]',
                    'EclLon': 'heliocentr. ecl. long. (deg, J2000.0) [float]',
                    'EclLat': 'heliocentr. ecl. lat.  (deg, J2000.0) [float]',
                    'r': 'heliocentric distance (au) [float]',
                    'r_rate': 'heliocentric radial rate (km/s) [float]',
                    'delta': 'distance from the observer (au) [float]',
                    'delta_rate': 'obs.-centric radial rate (km/s) [float]',
                    'lighttime': 'one-way light time (sec) [float]',
                    'elong': 'solar elongation (deg) [float]', 
                    'elongFlag': 'app. position relative to the Sun [string]',
                    'alpha': 'solar phase angle (deg) [float]',
                    'sunTargetPA': ('PA of Sun->target vector (deg, EoN) ' \
                                    + '[float]'),
                    'velocityPA': ('PA of velocity vector (deg, EoN) ' \
                                   + '[float]'),
                    'GlxLon': 'galactic longitude (deg) [float]',
                    'GlxLat': 'galactic latitude (deg) [float]',
                    'RA_3sigma': '3sigma pos. unc. in RA (arcsec) [float]',
                    'DEC_3sigma': '3sigma pos. unc. in DEC (arcsec) [float]',
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
            return "don't know key '%s'" % key





##### Example Code (just uncomment some of the following lines)

# import callhorizons

# # obtain ephemerides for Ceres
# ceres = callhorizons.query('Ceres')
# ceres.set_timerange('2016-02-23 00:00', '2016-02-24 00:00', '1h')
# print ceres.get_ephemerides(568)

# print ceres
# print ceres.fields
# print ceres.dates[ceres['solar_presence'] == 'dark']
# print ceres.whatis('solar_presence')

# # obtain orbital elements for Ceres
# print ceres.get_elements()
# print ceres.fields
# print ceres.dates_jd

# # export orbital elements for Ceres to PyEphem and use it to
# # determine rise, transit, and set times
# ceres_pyephem = ceres.export2pyephem()

# # PyEphem code (see http://rhodesmill.org/pyephem/quick.html)
# import ephem
# nau = ephem.Observer() # setup observer site
# nau.lon = -111.653152/180.*numpy.pi
# nau.lat = 35.184108/180.*numpy.pi
# nau.elevation = 2100 # m
# nau.date = '2015/10/5 01:23' # UT 
# print ('next rise: %s\n' % nau.next_rising(ceres_pyephem[0])), \
#     ('next transit: %s\n' % nau.next_transit(ceres_pyephem[0])), \
#     ('next setting: %s' % nau.next_setting(ceres_pyephem[0]))


