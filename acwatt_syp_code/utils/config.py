#!/usr/bin/env python
# Python 3.7
# File name: config.py
# Authors: Aaron Watt
# Date: 2021-11-03
"""Module to be imported for project settings and paths."""

# Built-in Imports
from pathlib import Path
import keyring
import logging
import keyring.util.platform_ as keyring_platform


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
        self.epa = self.root / 'epa'
        self.gis = self.root / 'gis'
        self.gis_county = self.gis / 'cb_2018_us_county_500k' / 'cb_2018_us_county_500k.shp'
        self.gis_state = self.gis / 'cb_2018_us_state_5m' / 'cb_2018_us_state_5m.shp'
        self.gis_windspeed = self.gis / 'windspeed'
        self.purpleair = self.root / 'purpleair'
        self.tables = self.root / 'tables'
        self.temp = self.root / 'temp'
        self.test_data = self.root / 'test_data'
        # Lookup tables
        self.lookup_location = self.tables / 'tbl_location_lookup.csv'
        self.lookup_fips = self.tables / 'tbl_fips_lookup.csv'

        self.make_directories()

    def make_directories(self):
        for _, path in self.__dict__.items():
            if path.suffix == '':
                path.mkdir(parents=True, exist_ok=True)


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
        self.url = 'https://api.purpleair.com/v1/sensors'
        namespace = "purpleair_api"
        self.read_key = None  # placeholder to be filled in below

        for attr in ["read_key"]:
            set_password(self, attr, namespace)


class AWSSettings:
    """Class to hold settings for Amazon AWS info."""
    def __init__(self):
        namespace = "aws_purpleair_downloader"
        self.bucket_arn = 'arn:aws:s3:::purpleair-data/*'
        self.bucket_name = 'purpleair-data'
        self.region = 'us-west-1'  # Northern CA
        self.python_version = '3.8'
        self.account_id = None  # placeholder for autocomplete, to be filled in below
        self.access_key = None
        self.secret_key = None

        for attr in ["account_id", "access_key", "secret_key"]:
            set_password(self, attr, namespace)


# FUNCTIONS --------------------------
def start_log():
    format_ = '%(asctime)s (%(levelname)s) %(name)s: %(message)s'
    datetime_ = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(filename='main.log', filemode='w', level=logging.INFO, format=format_, datefmt=datetime_)
    formatter = logging.Formatter(format_, datefmt=datetime_)
    streamer = logging.StreamHandler()
    streamer.setFormatter(formatter)
    streamer.setLevel(logging.INFO)
    logging.getLogger().addHandler(streamer)


def set_password(self, attr, namespace):
    try:
        value = keyring.get_credential(namespace, attr).password
        if value is None:
            raise AttributeError
    except AttributeError:
        value = input(f"Please paste your {namespace} {attr.replace('_', ' ')} here\n"
                      "This will be saved to your computer's encrypted keyring:")
        keyring.set_password(namespace, attr, value)
    setattr(self, attr, value)


# MAIN -------------------------------
# Create instances of each class to be called from other
PATHS = Paths()
GIS = GISSettings()
PA = PurpleAirSettings()
AWS = AWSSettings()
start_log()
YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021]
