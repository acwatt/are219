#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import pandas as pd
# Third-party Imports
# Local Imports
from ..utils.config import PATHS

threshold = 5  # miles
# For each EPA site-county in list
lookup_dir = PATHS.data.tables / 'epa_pa_lookups'
county, site = "037", "4004"  # start with one site
# Load sensor list for this site
sensor_list = pd.read_csv(lookup_dir / f'county-{county}_site-{site}_pa-list.csv')
sensor_list = sensor_list.query(f"dist_mile < {threshold}")
# For each sensor in list, download CSV from S3 to get PM2.5 values





