#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
# Third-party Imports
from ratelimiter import RateLimiter
# Local Imports
from ..utils.config import PATHS


def latlon_distance(x1, y1, x2, y2):
    return ((x1-x2)**2 + (y1-y2)**2)**0.5


def distance_from(center: dict, lat: np.float64, lon: np.float64):
    return latlon_distance(center['lat'], center['lon'], lat, lon)


@RateLimiter(max_calls=1, period=6)
def get_monitors_in_state(state: str, bdate: str, edate: str):
    param = 88101  # parameter key for NAAQS PM2.5 sensors
    url = f"https://aqs.epa.gov/data/api/monitors/byState?email={EPA.user_id}&key={EPA.read_key}&param={param}&bdate={bdate}&edate={edate}&state={state}"
    response = requests.get(url)
    df = pd.DataFrame(response.json()['Data'])
    # plot_ca_monitors(df)
    print(f"Open Date Range: {df.open_date.min()} - {df.open_date.max()}")
    print(f"Last Method Begin Date Range: {df.last_method_begin_date.min()} - {df.last_method_begin_date.max()}")
    return df


def load_monitors_from_file():
    p = PATHS.data.epa / "epa_monitors" / "epa_monitors" / "aqs_monitors.csv"
    df = pd.read_csv(p, low_memory=False,
                     dtype={"Parameter Code": int, "State Code": str, "County Code": str, "Site Number": str})
    df = (df
          .query("`Parameter Code` == 88101 and `NAAQS Primary Monitor` == 'Y'")
          .query("`Last Sample Date` > '2016-01-01' and `First Year of Data` < 2018")
          .drop(["Monitoring Objective", "Exclusions", "Local Site Name"], axis=1))  # drop b/c semicolon was messing up delimination of columns in csv
    return df


def load_monitors_from_api():
    df = get_monitors_in_state(state="06", bdate="20150101", edate="20200101")
    df2 = (df
          .query("naaqs_primary_monitor == 'Y'")
          .query("last_method_begin_date > '2016-01-01' and open_date < '2018-01-01'")
          .drop(["monitoring_objective", "concurred_exclusions", "local_site_name"], axis=1))
    print(f"all CA 88101 monitors: {len(df)}")  # drop b/c semicolon was messing up delimination of columns in csv
    print(f"filtered CA 88101 monitors: {len(df2)}")
    return df2


def save_pm25_locations(small_sample=False, n=50):
    # This is near a "interesting" sensor in LA, from Mu et al. (2021)
    center = {'lon': -118.17495969249252, 'lat': 33.79567453746542}
    # filepaths
    p2 = PATHS.data.epa / "epa_monitors" / "epa_monitors" / "aqs_monitors_88101_primary.csv"
    p3 = PATHS.data.epa / "epa_monitors" / "epa_monitors" / "aqs_monitors_88101_fullsample.csv"
    p4 = PATHS.data.epa / "epa_monitors" / "epa_monitors" / "aqs_monitors_88101_smallsample.csv"
    # Query data
    # load_monitors_from_file()
    df = load_monitors_from_api()
    # plot_ca_monitors(df)
    # Save full dataset
    df.to_csv(p2, index=False)
    # Save only needed columns of full dataset
    cols_to_keep = ["site_number", "latitude", "longitude", "datum",
                    "state_code", "county_code", "city_name",
                    'open_date', 'last_method_begin_date']
    df.to_csv(p3, columns=cols_to_keep, index=False)
    # calculate distance to point of interest (in LA)
    df = df.assign(distance=distance_from(center, df.Latitude, df.Longitude))
    # Pick top n closest points
    df2 = df.sort_values('distance', ascending=True).head(n)
    # Save only needed columns of small sample dataset
    df2.to_csv(p4, columns=cols_to_keep, index=False)
    fig = plt.Figure()
    plt.scatter(df.Longitude, df.Latitude, c='grey')
    plt.scatter(df2.Longitude, df2.Latitude, c='green')
    plt.scatter(-118.17495969249252, 33.79567453746542, c='red')
    if small_sample:
        return p4  # small sample file path
    else:
        return p3  # full sample file path

