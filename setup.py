"""setup function for CALLHORIZONS module"""

from setuptools import setup, find_packages

setup(
    name = "CALLHORIZONS",
    version = "1.0.9",
    author = "Michael Mommert",
    author_email = "michael.mommert@nau.edu",
    description = "CALLHORIZONS is a Python interface to access JPL HORIZONS ephemerides and orbital elements of Solar System bodies.",
    license = "MIT",
    keywords = "solar system, ephemerides, ephemeris, orbital elements, pyephem, asteroids, planets, spacecraft",
    url = "https://github.com/mommermi/callhorizons",
    packages=['callhorizons'],
    requires=['numpy'],
    test_suite='tests', 
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
