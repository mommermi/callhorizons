"""setup function for CALLHORIZONS module"""

from setuptools import setup

setup(
    name = "CALLHORIZONS",
    version = "0.9.1",
    author = "Michael Mommert",
    author_email = "michael.mommert (at) nau.edu",
    description = "CALLHORIZONS is a Python 2.7 interface to access JPL HORIZONS ephemerides and orbital elements of Solar System bodies.",
    license = "MIT",
    keywords = "solar system, ephemerides, ephemeris, orbital elements, pyephem",
    url = "https://github.com/mommermi/callhorizons",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
)
