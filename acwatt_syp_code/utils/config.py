#!/usr/bin/env python
# Python 3.7
# File name: config.py
# Authors: Aaron Watt
# Date: 2021-11-03
"""Module to be imported for project settings and paths."""

# Built-in Imports
from pathlib import Path


# CLASSES --------------------------
class Paths:
    """Inner paths class to store project paths commonly used.

    This will search the current working directory path for the name of the
    repo (beecensus). Since this code is only called from main.py, and main.py
    is inside the repo, it should be able to find the beecensus path.
    This also means the name of the repo cannot be changed.
    Since this is an inner class, paths will be accessible in the following way:
    Project = ProjectSettings()  # instance of the outer class
    Project.paths.root  # this will be the pathlib path to the github repo root
    """
    def __init__(self):
        # add root path of the project / git repo
        self.root = Path(*Path.cwd().parts[:Path.cwd().parts.index('are219') + 1])
        # Top-level paths
        self.code = self.root / 'acwatt_syp_code'
        self.docs = self.root / 'docs'
        self.output = self.root / 'output'
        self.paper = self.root / 'paper'
        # Data directories
        self.data = Data(self.root / 'data')


class Data:
    """Inner inner paths class to store data file paths."""
    def __init__(self, data_dir):
        self.root = data_dir
        self.checkpoints = self.root / 'checkpoints'
        self.configs = self.root / 'configs'
        self.gis = self.root / 'gis'
        self.gis_county = self.gis / 'cb_2018_us_county_500k' / 'cb_2018_us_county_500k.shp'
        self.gis_state = self.gis / 'cb_2018_us_state_5m' / 'cb_2018_us_state_5m.shp'
        self.purpleair = self.root / 'purpleair'
        self.tables = self.root / 'tables'
        self.temp = self.root / 'temp'
        self.test_data = self.root / 'test_data'
        # Lookup tables
        self.lookup_jpg = self.tables / 'tbl_jpg_lookup.csv'
        self.lookup_fips = self.tables / 'tbl_fips_lookup.csv'


class GISSettings:
    """Class to hold settings for gis portion of project.

    Possible geographical names:
        - Philadelphia County, PA
    """
    def __init__(self):
        # Name of geographical area to be used in the search for bees.
        self.geographical_name = 'California'


class PurpleAirSettings:
    """Class to hold settings for Purple Air API when downloading data."""
    def __init__(self):
        pass


# FUNCTIONS --------------------------


# MAIN -------------------------------
# Create instances of each class to be called from other
PATHS = Paths()
GIS = GISSettings()
PA = PurpleAirSettings()
