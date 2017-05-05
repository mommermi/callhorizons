"""setup function for CALLHORIZONS module"""

from setuptools import setup

setup(
    name = "CALLHORIZONS",
    version = "1.0.4",
    author = "Michael Mommert",
    author_email = "michael.mommert (at) nau.edu",
    description = "CALLHORIZONS is a Python interface to access JPL HORIZONS ephemerides and orbital elements of Solar System bodies.",
    license = "MIT",
    keywords = "solar system, ephemerides, ephemeris, orbital elements, pyephem, asteroids, planets, spacecraft",
    url = "https://github.com/mommermi/callhorizons",
    packages=['callhorizons'],
    requires=['numpy'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
)
