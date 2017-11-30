"""CALLHORIZONS - a Python interface to access JPL HORIZONS
ephemerides and orbital elements.

This module provides a convenient python interface to the JPL
HORIZONS system by directly accessing and parsing the HORIZONS
website. Ephemerides can be obtained through get_ephemerides,
orbital elements through get_elements. Function
export2pyephem provides an interface to the PyEphem module.

michael.mommert (at) nau.edu, latest version: v1.0.5, 2017-05-05.
This code is inspired by code created by Alex Hagen.

* v1.0.5: 15-epoch limit for set_discreteepochs removed
* v1.0.4: improved asteroid and comet name parsing
* v1.0.3: ObsEclLon and ObsEclLat added to get_ephemerides
* v1.0.2: Python 3.5 compatibility implemented
* v1.0.1: get_ephemerides fixed
* v1.0:   bugfixes completed, planets/satellites accessible, too
* v0.9:   first release


"""

from __future__ import (print_function, unicode_literals)

import re
import time
import numpy as np
try:
    # Python 3
    import urllib.request as urllib
except ImportError:
    # Python 2
    import urllib2 as urllib


def _char2int(char):
    """ translate characters to integer values (upper and lower case)"""
    if char.isdigit():
        return int(float(char))
    if char.isupper():
        return int(char, 36)
    else:
        return 26 + int(char, 36)


class query():

    ### constructor

    def __init__(self, targetname, smallbody=True, cap=True, comet=False,
                 asteroid=False):
        """
        Initialize query to Horizons

        :param targetname: HORIZONS-readable target number, name, or designation
        :param smallbody:  boolean  use ``smallbody=False`` if targetname is a 
                           planet or spacecraft (optional, default: `True`); 
                           also use `True` if the targetname is exact and 
                           should be queried as is
        :param cap: boolean set to `True` to return the current apparition for 
                    comet targets
        :param comet: set to `True` if this is a comet (will override 
                      automatic targetname parsing)
        :param asteroid: set to `True` if this is an asteroid (will override 
                         automatic targetname parsing)
        :return: None
        """

        self.targetname     = str(targetname)
        self.not_smallbody  = not smallbody
        self.cap            = cap
        self.comet = comet # is this object a comet?
        self.asteroid = asteroid  # is this object an asteroid?
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

        :return: (string or None, int or None, string or None);
          The designation, number and prefix, and name of the comet as derived 
          from `self.targetname` are extracted into a tuple; each element that 
          does not exist is set to `None`. Parenthesis in `self.targetname` 
          will be ignored.
        :example: the following table shows the result of the parsing:
     
        +--------------------------------+--------------------------------+
        |targetname                      |(desig, prefixnumber, name)     |
        +================================+================================+
        |1P/Halley                       |(None, '1P', 'Halley')          |
        +--------------------------------+--------------------------------+
        |3D/Biela                        |(None, '3D', 'Biela')           |
        +--------------------------------+--------------------------------+
        |9P/Tempel 1                     |(None, '9P', 'Tempel 1')        |
        +--------------------------------+--------------------------------+
        |73P/Schwassmann Wachmann 3 C    |(None, '73P',                   |
        |                                |'Schwassmann Wachmann 3 C')     |
        +--------------------------------+--------------------------------+
        |73P-C/Schwassmann Wachmann 3 C  |(None, '73P-C',                 |
        |                                |'Schwassmann Wachmann 3 C')     |
        +--------------------------------+--------------------------------+
        |73P-BB                          |(None, '73P-BB', None)          |
        +--------------------------------+--------------------------------+
        |322P                            |(None, '322P', None)            |
        +--------------------------------+--------------------------------+
        |X/1106 C1                       |('1166 C1', 'X', None)          |
        +--------------------------------+--------------------------------+
        |P/1994 N2 (McNaught-Hartley)    |('1994 N2', 'P',                |
        |                                |'McNaught-Hartley')             |
        +--------------------------------+--------------------------------+
        |P/2001 YX127 (LINEAR)           |('2001 YX127', 'P', 'LINEAR')   |
        +--------------------------------+--------------------------------+
        |C/-146 P1                       |('-146 P1', 'C', None)          |
        +--------------------------------+--------------------------------+
        |C/2001 A2-A (LINEAR)            |('2001 A2-A', 'C', 'LINEAR')    |
        +--------------------------------+--------------------------------+
        |C/2013 US10                     |('2013 US10', 'C', None)        |
        +--------------------------------+--------------------------------+
        |C/2015 V2 (Johnson)             |('2015 V2', 'C', 'Johnson')     |
        +--------------------------------+--------------------------------+
        """

        import re

        pat = ('^(([1-9]+[PDCXAI](-[A-Z]{1,2})?)|[PDCXAI]/)' + # prefix [0,1,2]
               '|([-]?[0-9]{3,4}[ _][A-Z]{1,2}[0-9]{1,3}(-[1-9A-Z]{0,2})?)' +
               # designation [3,4]
               ('|(([A-Z][a-z]?[A-Z]*[a-z]*[ -]?[A-Z]?[1-9]*[a-z]*)' +
                '( [1-9A-Z]{1,2})*)') # name [5,6]
               )
        
        m = re.findall(pat, self.targetname.strip())

        #print(m)
        
        prefixnumber = None
        desig = None
        name = None

        if len(m) > 0:
            for el in m:
                # prefix/number
                if len(el[0]) > 0:
                    prefixnumber = el[0].replace('/', '')
                # designation
                if len(el[3]) > 0:
                    desig = el[3].replace('_', ' ')
                # name
                if len(el[5]) > 0:
                    if len(el[5]) > 1:
                        name = el[5]

        return (desig, prefixnumber, name)

    def parse_asteroid(self):
        """Parse `targetname` as if it were a asteroid.
        
        :return: (string or None, int or None, string or None);
          The designation, number, and name of the asteroid as derived from 
          `self.targetname` are extracted into a tuple; each element that 
          does not exist is set to `None`. Parenthesis in `self.targetname` 
          will be ignored. Packed designations and numbers are unpacked. 
        :example: the following table shows the result of the parsing:

        +--------------------------------+---------------------------------+
        |targetname                      |(desig, number, name)            |
        +================================+=================================+
        |1                               |(None, 1, None)                  |
        +--------------------------------+---------------------------------+
        |2 Pallas                        |(None, 2, Pallas)                |
        +--------------------------------+---------------------------------+
        |\(2001\) Einstein               |(None, 2001, Einstein)           |
        +--------------------------------+---------------------------------+
        |1714 Sy                         |(None, 1714, Sy)                 |
        +--------------------------------+---------------------------------+
        |2014 MU69                       |(2014 MU69, None, None)          |
        +--------------------------------+---------------------------------+
        |(228195) 6675 P-L               |(6675 P-L, 228195, None)         |
        +--------------------------------+---------------------------------+
        |4101 T-3                        |(4101 T-3, None, None)           |
        +--------------------------------+---------------------------------+
        |4015 Wilson-Harrington (1979 VA)|(1979 VA, 4015, Wilson-Harrington|
        +--------------------------------+---------------------------------+
        |J95X00A                         |(1995 XA, None, None)            |
        +--------------------------------+---------------------------------+
        |K07Tf8A                         |(2007 TA418, None, None)         |
        +--------------------------------+---------------------------------+
        |G3693                           |(None, 163693, None)             |
        +--------------------------------+---------------------------------+
        |2017 U1                         |(None, None, None)               |
        +--------------------------------+---------------------------------+
        """

        pat = ('(([1-2][0-9]{0,3}[ _][A-Z]{2}[0-9]{0,3})' # designation [0,1]
               '|([1-9][0-9]{3}[ _](P-L|T-[1-3])))' # Palomar-Leiden  [0,2,3]
               '|([IJKL][0-9]{2}[A-Z][0-9a-z][0-9][A-Z])' # packed desig [4]
               '|([A-Za-z][0-9]{4})' # packed number [5]
               '|([A-Z][A-Z]*[a-z][a-z]*[^0-9]*'
                 '[ -]?[A-Z]?[a-z]*[^0-9]*)' # name [6]
               '|([1-9][0-9]*(\b|$))') # number [7,8]

        # regex patterns that will be ignored as they might cause
        # confusion
        non_pat = ('([1-2][0-9]{0,3}[ _][A-Z][0-9]*(\b|$))') # comet desig 

        raw = self.targetname.translate(str.maketrans('()', '  ')).strip()

        # reject non_pat patterns
        non_m = re.findall(non_pat, raw)
        #print('reject', raw, non_m)
        if len(non_m) > 0:
            for ps in non_m:
                for p in ps:
                    if p == '':
                        continue
                    raw = raw[:raw.find(p)] + raw[raw.find(p)+len(p):]

        # match target patterns
        m = re.findall(pat, raw)
        
        #print(raw, m)
        
        desig = None
        number = None
        name = None

        if len(m) > 0:
            for el in m:
                # designation
                if len(el[0]) > 0:
                    desig = el[0]
                # packed designation (unpack here)
                elif len(el[4]) > 0:
                    ident = el[4]
                # old designation style, e.g.: 1989AB
                    if (len(ident.strip()) < 7 and ident[:4].isdigit() and
                        ident[4:6].isalpha()):
                        desig = ident[:4]+' '+ident[4:6]
                        # Palomar Survey
                    elif ident.find("PLS") == 0:
                        desig = ident[3:] + " P-L"
                        # Trojan Surveys
                    elif ident.find("T1S") == 0:
                        desig = ident[3:] + " T-1"   
                    elif ident.find("T2S") == 0:
                        desig = ident[3:] + " T-2"   
                    elif ident.find("T3S") == 0:
                        desig = ident[3:] + " T-3"   
                    # insert blank in designations
                    elif (ident[0:4].isdigit() and ident[4:6].isalpha() and
                          ident[4] != ' '):
                        desig = ident[:4]+" "+ident[4:]
                    # MPC packed 7-digit designation
                    elif (ident[0].isalpha() and ident[1:3].isdigit() and
                          ident[-1].isalpha() and ident[-2].isdigit()):
                        yr = str(_char2int(ident[0]))+ident[1:3]
                        let = ident[3]+ident[-1]
                        num = str(_char2int(ident[4]))+ident[5]
                        num = num.lstrip("0")
                        desig = yr+' '+let+num
                    # nothing to do
                    else:
                        desig = ident
                # packed number (unpack here)
                elif len(el[5]) > 0:
                    ident = el[5]
                    number = ident = int(str(_char2int(ident[0]))+ident[1:])
                # number
                elif len(el[7]) > 0:
                    number = int(float(el[7].translate(str.maketrans('()',
                                                                     '  '))))
                # name (strip here)
                elif len(el[6]) > 0:
                    if len(el[6].strip()) > 1:
                        name = el[6].strip()

        return (desig, number, name)

                    
    def isorbit_record(self):
        """`True` if `targetname` appears to be a comet orbit record number.

        NAIF record numbers are 6 digits, begin with a '9' and can
        change at any time.

        """

        import re
        test = re.match('^9[0-9]{5}$', self.targetname.strip()) is not None
        return test

    def iscomet(self):
        """`True` if `targetname` appears to be a comet. """

        # treat this object as comet if there is a prefix/number
        if self.comet == True:
            return true
        else:
            return (self.parse_comet()[0] is not None or
                    self.parse_comet()[1] is not None)

    def isasteroid(self):
        """`True` if `targetname` appears to be an asteroid."""
        if self.asteroid == True:
            return True
        else:
            return any(self.parse_asteroid()) is not None

    ### set epochs

    def set_epochrange(self, start_epoch, stop_epoch, step_size):

        """Set a range of epochs, all times are UT

        :param start_epoch: str;
           start epoch of the format 'YYYY-MM-DD [HH-MM-SS]'
        :param stop_epoch: str;
           final epoch of the format 'YYYY-MM-DD [HH-MM-SS]'
        :param step_size: str;
           epoch step size, e.g., '1d' for 1 day, '10m' for 10 minutes...
        :return: None
        :example: >>> import callhorizons
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

        :param discreteepochs: array_like
           list or 1D array of floats or strings
        :return: None
        :example: >>> import callhorizons
                  >>> ceres = callhorizons.query('Ceres')
                  >>> ceres.set_discreteepochs([2457446.177083, 2457446.182343])
        """
        if not isinstance(discreteepochs, (list, np.ndarray)):
            discreteepochs = [discreteepochs]

        self.discreteepochs = list(discreteepochs)


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

        :param key: str/int;
           epoch index or property key
        :return: query data according to key
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

        :param observatory_code: str/int;
           observer's location code according to Minor Planet Center
        :param airmass_lessthan: float;
           maximum airmass (optional, default: 99)
        :param solar_elongation: tuple;
           permissible solar elongation range (optional, deg)
        :param skip_daylight: boolean;
           crop daylight epoch during query (optional)
        :result: int; number of epochs queried
        :example: >>> ceres = callhorizons.query('Ceres')
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
        elif self.iscomet() and not self.asteroid:
            # for comets, potentially append the current apparition
            # (CAP) parameter
            for ident in self.parse_comet():
                if ident is not None:
                    break
            if ident is None:
                ident = self.targetname
            url += "&COMMAND='DES=" + \
                   urllib.quote(ident.encode("utf8")) + "%3B" + \
                   ("CAP'" if self.cap else "'")
        elif self.isasteroid():
            # for asteroids, use 'DES="designation";'
            for ident in self.parse_asteroid():
                if ident is not None:
                    break
            if ident is None:
                ident = self.targetname
            url += "&COMMAND='" + \
                   urllib.quote(str(ident).encode("utf8")) + "%3B'"
        # elif (not self.targetname.replace(' ', '').isalpha() and not
        #      self.targetname.isdigit() and not
        #      self.targetname.islower() and not
        #      self.targetname.isupper()):
        #     # lower case + upper case + numbers = pot. case sensitive designation
        #     url += "&COMMAND='DES=" + \
        #            urllib.quote(self.targetname.encode("utf8")) + "%3B'"
        else:
            url += "&COMMAND='" + \
                   urllib.quote(self.targetname.encode("utf8")) + "%3B'"

        if self.discreteepochs is not None:
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
                    try:
                        H = float(HGline[1].rstrip('G'))
                    except ValueError:
                        pass
                    try:
                        G = float(HGline[2].rstrip('B-V'))
                    except ValueError:
                        pass
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
                    this_eph.append({'/L':'leading', '/T':'trailing',
                                     '/?':'not defined'}\
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




    def get_elements(self, center='500@10', asteroid=False, comet=False):
        """Call JPL HORIZONS website to obtain orbital elements based on the
        provided targetname, epochs, and center code. For valid center
        codes, please refer to http://ssd.jpl.nasa.gov/horizons.cgi

        :param center:  str; 
           center body (default: 500@10 = Sun)
        :result: int; number of epochs queried
        :example: >>> ceres = callhorizons.query('Ceres')
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
        elif self.isorbit_record():
            # Comet orbit record. Do not use DES, CAP. This test must
            # occur before asteroid test.
            url += "&COMMAND='" + \
                   urllib.quote(self.targetname.encode("utf8")) + "%3B'"
        elif self.iscomet():
            # for comets, potentially append the current apparition
            # (CAP) parameter
            for ident in self.parse_comet():
                if ident is not None:
                    break
            if ident is None:
                ident = self.targetname
            url += "&COMMAND='DES=" + \
                   urllib.quote(str(ident).encode("utf8")) + "%3B" + \
                   ("CAP'" if self.cap else "'")
        elif self.isasteroid():
            # for asteroids, use 'DES="designation";'
            for ident in self.parse_asteroid():
                if ident is not None:
                    break
            if ident is None:
                ident = self.targetname
            url += "&COMMAND='" + \
                   urllib.quote(ident.encode("utf8")) + "%3B'"
        # elif (not self.targetname.replace(' ', '').isalpha() and not
        #      self.targetname.isdigit() and not
        #      self.targetname.islower() and not
        #      self.targetname.isupper()):
        #     url += "&COMMAND='DES=" + str(objectname) + "%3B'"
        else:
            url += "&COMMAND='" + str(objectname) + "%3B'"


        if self.discreteepochs is not None:
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
                    try:
                        H = float(HGline[1].rstrip('G'))
                    except ValueError:
                        pass
                    try:
                        G = float(HGline[2].rstrip('B-V'))
                    except ValueError:
                        pass
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

        :param center: str;
           center body (default: 500@10 = Sun)
        :param equinox: float;
           equinox (default: 2000.0)
        :result: list;
           list of PyEphem objects, one per epoch
        :example: >>> import callhorizons
                  >>> import numpy
                  >>> import ephem
                  >>>
                  >>> ceres = callhorizons.query('Ceres')
                  >>> ceres.set_epochrange('2016-02-23 00:00', '2016-02-24 00:00', '1h')
                  >>> ceres_pyephem = ceres.export2pyephem()
                  >>>
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


