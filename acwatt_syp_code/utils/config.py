#!/usr/bin/env python
# Python 3.7
# File name: config.py
# Authors: Aaron Watt
# Date: 2021-11-03
"""Module to be imported for project settings and paths."""

# Built-in Imports
from pathlib import Path
import keyring
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
        self.purpleair = self.root / 'purpleair'
        self.tables = self.root / 'tables'
        self.temp = self.root / 'temp'
        self.test_data = self.root / 'test_data'
        # Lookup tables
        self.lookup_location = self.tables / 'tbl_location_lookup.csv'
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
        self.url = 'https://api.purpleair.com/v1/sensors'
        namespace = "purpleair_api"
        try:
            self.read_key = keyring.get_credential(namespace, "read_key").password
            # self.write_key = keyring.get_credential(namespace, "write_key").password
            # Write key not used currently
        except AttributeError:
            self.read_key = input("Please paste your PurpleAir read key here\n"
                               "This will be saved to your computer's encrypted keyring:")
            keyring.set_password(namespace, "read_key", self.read_key)
            # self.write_key = input("Please paste your PurpleAir write key here\n"
            #                    "This will be saved to your computer's encrypted keyring:")
            # keyring.set_password(namespace, "write_key", self.write_key)


class AWSSettings:
    """Class to hold settings for Amazon AWS info."""
    def __init__(self):
        namespace = "aws_purpleair_downloader"
        self.bucket_arn = 'arn:aws:s3:::purpleair-data/*'
        self.bucket_name = 'purpleair-data'
        self.region = 'us-west-1'  # Northern CA
        try:
            self.account_id = keyring.get_credential(namespace, "account_id").password
            self.access_key = keyring.get_credential(namespace, "access_key").password
            self.secret_key = keyring.get_credential(namespace, "secret_key").password
        except AttributeError:
            self.access_key = input("Please paste your AWS IAM role access key here\n"
                               "This will be saved to your computer's encrypted keyring:")
            self.secret_key = input("Please paste your AWS IAM role secret key here\n"
                               "This will be saved to your computer's encrypted keyring:")
            keyring.set_password(namespace, "access_key", self.access_key)
            keyring.set_password(namespace, "secret_key", self.secret_key)


# FUNCTIONS --------------------------


# MAIN -------------------------------
# Create instances of each class to be called from other
PATHS = Paths()
GIS = GISSettings()
PA = PurpleAirSettings()
AWS = AWSSettings()
