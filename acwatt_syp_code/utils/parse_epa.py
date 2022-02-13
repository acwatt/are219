#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Third-party Imports
# Local Imports
from ..utils.config import PATHS


def latlon_distance(x1, y1, x2, y2):
    return ((x1-x2)**2 + (y1-y2)**2)**0.5


def distance_from(center: dict, lat: np.float64, lon: np.float64):
    return latlon_distance(center['lat'], center['lon'], lat, lon)


def save_pm25_locations(small_sample=False, n=10):
    # This is near a "interesting" sensor in LA, from Mu et al. (2021)
    center = {'lon': -118.17495969249252, 'lat': 33.79567453746542}
    # filepaths
    p = PATHS.data.epa / "epa_monitors" / "epa_monitors" / "aqs_monitors.csv"
    p2 = PATHS.data.epa / "epa_monitors" / "epa_monitors" / "aqs_monitors_88101primary.csv"
    p3 = PATHS.data.epa / "epa_monitors" / "epa_monitors" / "aqs_monitors_88101_fullsample.csv"
    p4 = PATHS.data.epa / "epa_monitors" / "epa_monitors" / "aqs_monitors_88101_smallsample.csv"
    # Query data
    df = (pd.read_csv(p, low_memory=False,
                      dtype={"Parameter Code": int, "State Code": str, "County Code": str, "Site Number": str})
          .query("`Parameter Code` == 88101 and `NAAQS Primary Monitor` == 'Y'")
          .drop(["Monitoring Objective", "Exclusions", "Local Site Name"], axis=1))  # drop b/c semicolon was messing up delimination of columns in csv
    # Save full dataset
    df.to_csv(p2, index=False)
    # Save only needed columns of full dataset
    cols_to_keep = ["Site Number", "Latitude", "Longitude", "Datum", "State Code", "County Code", "City Name"]
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

