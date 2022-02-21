#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import json
import pandas as pd
from pandas.core.computation.ops import UndefinedVariableError
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point
import requests
import matplotlib.pyplot as plt
# Third-party Imports
from ratelimiter import RateLimiter
# Local Imports
from ..utils.config import PATHS, EPA
PATHS.data.epa_monitors = PATHS.data.epa / 'epa_monitors' / 'epa_monitors'
PATHS.data.epa_pm25 = PATHS.data.epa_monitors / 'data_from_api' / '88101'
DTYPES = {"parameter_code": int, "state_code": str, "county_code": str, "site_number": str}


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


def save_site(site, county, years = None):
    p = PATHS.data.epa_pm25 / f"county-{county}_site-{site}_hourly.csv"
    # Check if file already exists
    if p.exists():
        return False
    else:
        print("Downloading hourly EPA data for", site, county)
    if years is None:
        years = ['2016', '2017', '2018', '2019', '2020', '2021']
    df_list = []
    # For each year, get site-year hourly data
    for year in years:
        df_temp = get_site_year(site, year, county=county)
        df_list.append(df_temp)
        print(df_temp)
    # Concat df_list and save site-hourly file
    df_site_hourly = pd.concat(df_list)
    df_site_hourly = (df_site_hourly
                      .query("sample_duration == '1 HOUR'")
                      .sort_values(['date_local', 'time_local']))
    df_site_hourly.to_csv(p, index=False)
    return True


def load_small_sample_ids():
    p = PATHS.data.epa.monitors / 'aqs_monitors_88101_smallsample.csv'
    df = pd.read_csv(p, dtype=DTYPES)
    sites = df['site_number'].to_list()
    counties = df['county_code'].to_list()
    return [pair for pair in zip(sites, counties)]


def load_pa_locations():
    # Load county shapefile to get CRS for purpleair locations
    p_shp = PATHS.data.gis / 'cb_2018_us_county_500k' / 'cb_2018_us_county_500k.shp'
    gdf = gpd.read_file(p_shp)
    p_pa = PATHS.data.temp / 'sensors_filtered.csv'
    cols = ['sensor_index', 'date_created', 'lat', 'lon', 'STUSPS', 'geometry']
    df = pd.read_csv(p_pa, usecols=cols)
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs=gdf.crs)
    gdf = gdf.rename(columns={'lat': 'latitude', 'lon': 'longitude', 'STUSPS': 'state'})
    gdf = gdf.query("state in ['CA', 'OR', 'NV', 'AZ']")
    return gdf


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


def plot_epa_pa_sensors(df1, point, site, county):
    p_shp = PATHS.data.gis / 'cb_2018_us_county_500k' / 'cb_2018_us_county_500k.shp'
    gdf = gpd.read_file(p_shp).query("STATEFP == '06'")
    ax = gdf.plot(color='grey', figsize=(8, 8))
    df1.to_crs(gdf.crs).plot(ax=ax, color='blue')
    # for thresh in [25, 10, 5]:
    #     df2 = df1.to_crs(gdf.crs).query(f"dist < {thresh}")
    #     df2.plot(ax=ax, color='green', alpha=0.1)
    df2 = df1.to_crs(gdf.crs).query("dist < 25")
    df2.plot(ax=ax, color='green')
    df2b = df1.to_crs(gdf.crs).query("dist < 10")
    df2b.plot(ax=ax, color='yellow')
    df2c = df1.to_crs(gdf.crs).query("dist < 5")
    df2c.plot(ax=ax, color='pink')
    df3 = gpd.GeoDataFrame(geometry=[point], crs='EPSG:3310').to_crs(gdf.crs)
    df3.plot(ax=ax, color='red')
    p_fig = PATHS.output / 'figures' / f'county-{county}_site-{site}_epa-pa-concentric-ranges.png'
    # Adjust the figure
    width, height = 0.55, 0.51
    plt.xlim([df3.geometry[0].x-width, df3.geometry[0].x+width])
    plt.ylim([df3.geometry[0].y-height, df3.geometry[0].y+height])
    plt.tight_layout()
    plt.savefig(p_fig)


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


def test():
    # load list of 15 hourly CA sites (county-site pair)
    p1 = PATHS.data.epa_monitors / 'aqs_monitors_88101_hourly-ca-monitors.csv'
    df1 = pd.read_csv(p1, dtype=DTYPES)
    site_counties = [pair for pair in zip(df1.site_number, df1.county_code)]

    # For each EPA site, download hourly data and save csv if it doesn't exist
    for site, county in site_counties:
        save_site(site, county)

    # Merge EPA site IDs with EPA site characteristics from small_sample
    p2 = PATHS.data.epa_monitors / 'aqs_monitors_88101_smallsample.csv'
    df2 = pd.read_csv(p2, dtype=DTYPES)
    df1 = df1.merge(df2, on=['county_code', 'site_number'], how='left')

    # Load CA PA sensors with locations
    df_pa = load_pa_locations()

    # for each EPA monitor
    # site, county, lat, lon = "4004", "037", 33.79236, -118.17533
    mile_to_meter = 1609.34

    for site, county, lat, lon in zip(df1.site_number, df1.county_code, df1.latitude, df1.longitude):
        print('Finding nearest PA sensors for', site, county)
        df_temp = df_pa.copy()
        # translate lat lon to meter coordinate system
        point = (gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs=df_pa.crs)
                 .to_crs('EPSG:3310')
                 .geometry[0])
        # calulate distance of all PA monitors to EPA site location
        df_temp = df_temp.to_crs('EPSG:3310')
        df_temp['dist'] = df_temp.geometry.distance(point) / mile_to_meter
        plot_epa_pa_sensors(df_temp, point, site, county)
        # get PA sensors within 25 miles
        pass

        # calulate non-normalized IDW weights for each PA monitor

        # add PA IDs, weights, EPA site, county to dataframe
    # Save dataframe to file (aqs_monitors_to_pa_sensors.csv)

    pa_complete_list = []
    # For each PA id in dataframe
    for
        # Download all PA data and save to PA-id csv

        # For each quarter from this PA's min(year) to max(year)
            # Calc quarter's hourly completeness and add to dataframe
            # Add quartly hourly completeness to list
            pa_complete_list.append({})

    # Save PA quarter hourly completeness (pa_epa_sensors_completeness.csv)

    # for each EPA site
        # load list of PA sensors and weights
        # for each quarter where more than 75% of hourly EPA obs exist
            # Add site-quarter to
            # Filter PA sensors for >X% completeness

            # For each hour in quarter
                # Create new weights for non-missing PA-hours (divide by sum of weights)

                # Create IDW weighted EPA predicted PM2.5 from PA-hours

            # Save # of total hours and # of missing EPA hours in quarter

            # Create design values for non-missing EPA

            # Create




""" EPA AQS API Notes
Request Limits and Terms of Service
The API has the following limits imposed on request size:
- Length of time: All services (except Monitor) must have the end date (edate field) be in the same year as the begin date (bdate field).
- Number of parameters: Most services allow for the selection of multiple parameter codes (param field). A maximum of 5 parameter codes may be listed in a single request.
- Limit the size of queries: Our database contains billions of values and you may request more than you intend. If you are unsure of the amount of data, start small and work your way up. We request that you limit queries to 1,000,000 rows of data each. You can use the "observation count" field on the annualData service to determine how much data exists for a time-parameter-geography combination. If you have any questions or need advice, please contact us.
- Limit the frequency of queries: Our system can process a limited load. If scripting requests, please wait for one request to complete before submitting another and do not make more than 10 requests per minute. Also, we request a pause of 5 seconds between requests and adjust accordingly for response time and size.
If you violate these terms, we may disable your account without notice (but we will be in contact via the email address provided).
"""



