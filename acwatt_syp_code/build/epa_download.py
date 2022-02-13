#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import json
import pandas as pd
import requests
# Third-party Imports
# Local Imports
from ..utils.config import PATHS, EPA


def get_monitor_list_at_site(bdate: str, edate: str, state: str, county: str, site: str):
    """Returns list of PM2.5 monitors at {site} that operated between the bdate and edate

    bdate: (beginning date) date string of the form YYYYMMDD
    edate: see bdate
    state: The 2 digit state FIPS code for the state (with leading zero). They may be obtained via the list states service. Only data from within this state will be returned.
    county: The 3 digit state FIPS code for the county within the state (with leading zeroes). They may be obtained via the list counties service. Only data from within this county will be returned.
    site: The 4 digit AQS site number within the county (with leading zeroes). They may be obtained via the list sites service. Only data from this site will be returned.
    """
    param = 88101  # parameter key for NAAQS PM2.5 sensors
    url = f"https://aqs.epa.gov/data/api/monitors/bySite?email={EPA.user_id}&key={EPA.read_key}&param={param}&bdate={bdate}&edate={edate}&state={state}&county={county}&site={site}"
    response = requests.get(url)
    print(response.json()['Data'])
    # Filter for monitors with naaqs_primary_monitor == "Y"
    print()


def get_site_list(state: str, county: str):
    url = f"https://aqs.epa.gov/data/api/list/sitesByCounty?email={EPA.user_id}&key={EPA.read_key}&state={state}&county={county}"
    response = requests.get(url)
    print(response.json()['Data'])
    print()


def get_site_data(bdate: str, edate: str, state: str, county: str, site: str):
    param = 88101  # parameter key for NAAQS PM2.5 sensors
    url = f"https://aqs.epa.gov/data/api/sampleData/bySite?email={EPA.user_id}&key={EPA.read_key}&param={param}&bdate={bdate}&edate={edate}&state={state}&county={county}&site={site}"
    response = requests.get(url)
    d = response.json()['Data']
    df = pd.DataFrame(d)
    return df


def get_site_year(site, year, state="06", county="037"):
    bdate = f"{year}0101"
    edate = f"{year}1231"
    df = get_site_data(bdate=bdate, edate=edate, state=state, county=county, site=site)
    return df


def test():
    # get_monitor_list_at_site(bdate="20160101", edate="20210101", state="06",
    #                          county="037", site="4004")
    # get_site_list(state="06", county="037")
    # get_site_data(bdate="20160101", edate="20161231", state="06", county="037", site="4004")
    df = get_site_year("4004", "2016")
    for hour in range(24):
        h = f"{hour:02d}"
        print(hour, sum(df.query(f"time_local == '{h}:00' and sample_duration == '1 HOUR'").sample_measurement.isna()))
    print('done')



