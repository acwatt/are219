#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import json
import pandas as pd
from pandas.core.computation.ops import UndefinedVariableError
import requests
import matplotlib.pyplot as plt
# Third-party Imports
from ratelimiter import RateLimiter
# Local Imports
from ..utils.config import PATHS, EPA


@RateLimiter(max_calls=1, period=6)
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
    df = pd.DataFrame(response.json()['Data'])
    df = df.query("naaqs_primary_monitor == 'Y'")
    return df


@RateLimiter(max_calls=1, period=6)
def get_site_list(state: str, county: str):
    url = f"https://aqs.epa.gov/data/api/list/sitesByCounty?email={EPA.user_id}&key={EPA.read_key}&state={state}&county={county}"
    response = requests.get(url)
    print(response.json()['Data'])
    print()


@RateLimiter(max_calls=1, period=6)
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


def load_small_sample_ids():
    p = PATHS.data.epa.monitors / 'aqs_monitors_88101_smallsample.csv'
    df = pd.read_csv(p, dtype=DTYPES)
    sites = df['site_number'].to_list()
    counties = df['county_code'].to_list()
    return [pair for pair in zip(sites, counties)]


def plot_hour_distributions(df, site, year):
    for hour in range(24):
        h = f"{hour:02d}"
        print(hour, sum(df.query(f"time_local == '{h}:00' and sample_duration == '1 HOUR'").sample_measurement.isna()))
    p1 = (df
          .query("sample_frequency=='HOURLY'")
          .groupby('time_local')
          .mean()
          .reset_index()
          .plot(x='time_local', y='sample_measurement',
                xlabel='Hour of Day', ylabel='PM2.5 (hourly average)',
                title=f"PM2.5 Data for site {site} in {year}"))
    p2 = (df
          .query("sample_frequency=='HOURLY'")
          .groupby('time_local')
          .agg({'sample_measurement': lambda x: x.isnull().sum()})
          .rename(columns={'sample_measurement': 'Missing (count)'})
          .reset_index()
          .plot(x='time_local', y='Missing (count)', ax=p1, secondary_y=True))
    ax2 = p1.twinx()
    ax2.set_ylabel('Missing Observations (count)', color='b')
    plt.show()


def generate_observation_counts():
    # bdate, edate = "20160101", "20210101"
    # df_monitors = get_monitor_list_at_site(bdate=bdate, edate=edate, state="06",
    #                          county="037", site="4004")
    # get_site_list(state="06", county="037")
    # get_site_data(bdate="20160101", edate="20161231", state="06", county="037", site="4004")
    site_county_pairs = load_small_sample_ids()
    data_list = []
    for year in ['2016', '2017', '2018', '2019', '2020', '2021']:
        print('YEAR', year, '='*40)
        for site, county in site_county_pairs:
            df = get_site_year(site, year, county=county)
            try:
                obs_hourly = len(df.query("sample_duration == '1 HOUR'"))
            except (KeyError, UndefinedVariableError):
                obs_hourly = 0
            try:
                obs_daily = len(df.query("sample_duration == '24 HOUR'"))
            except (KeyError, UndefinedVariableError):
                obs_daily = 0
            print(site, obs_hourly, obs_daily)
            data_list.append({'year': year, 'site': site, 'county': county,
                              'number_hourly_obs': obs_hourly,
                              'number_daily_obs': obs_daily})
            # plot_hour_distributions(df, site, year)
    p = PATHS.data.epa.monitors / 'aqs_monitors_88101_hourlyobs.csv'
    pd.DataFrame(data_list).to_csv(p, index=False)
    print('done')



