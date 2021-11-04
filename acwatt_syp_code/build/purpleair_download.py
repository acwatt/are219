#!/usr/bin/env python

"""Functions to download purple air data via their API"""

# Built-in Imports
from datetime import datetime, timedelta
import json
import pandas as pd
# Third-party Imports
import purpleair.network as pan
from purpleair.network import SensorList, Sensor
# Local imports
from ..utils.config import PATHS


# If retrieving data from multiple sensors at once, please send a single request
# rather than individual requests in succession.


"""
PURPLE AIR PYTHON LIBRARY: https://github.com/ReagentX/purple_air_api
Conditions of use:
 License and copyright notice
 State changes
 Disclose source
 Same license
"""


def df_sensors():
    """Return list of sensors that have valid data."""
    p = pan.SensorList()  # Initialized 22,877 sensors!
    # Other sensor filters include 'outside', 'all', 'useful', 'family', and 'no_child'
    df = p.to_dataframe(sensor_filter='useful', channel='parent')
    return df


def filter_data(df):
    df = (df.query('location_type == "outside"')
          .query('downgraded == False')
          .query('flagged == False')
          )
    return df


def dl_pm25(sensor_list):
    """Save dataframe of PM 2.5 data from all valid sensors."""
    for s in sensor_list:
        pass


def dl_from_sensor(sensor_id, start_date=datetime.now()):
    df = (pan.Sensor(sensor_id)
          .parent.get_historical(weeks_to_get=1,
                                 thingspeak_field='secondary',
                                 start_date=start_date))
    return df


def dl_in_geo_area(gdf, start_date, num_weeks=10):
    """Download data from sensors in gdf between start_date and end_date.

    gdf = geopandas dataframe that has already been filtered for sensors within
        a geographic area using analyze.maps.sensor_df_to_geo()
    start_date, end_date = datetime.datetime date
    """
    # Request data from each sensor in num_week chunks
    beginning = datetime.today().date() - timedelta(weeks=num_weeks)
    # while beginning > start_date:
    #     for
    #
    #     beginning = beginning - timedelta(weeks=num_weeks)
    #     if beginning < start_date:
    #         beginning = start_date


def dl_id_by_date(id, end_date, num_weeks=10):
    """Return dataframe of historical sensor data for id between dates."""
    dfs = [(se
            .parent
            .get_historical(weeks_to_get=1, thingspeak_field='primary')
            .assign(sensor_id=se.identifier, channel='parent')
            .filter(cols_to_keep, axis=1)) for se in se2]


def dl_geo_by_date(gdf, start_date, end_date):
    """Download data from sensors in gdf between start_date and end_date.

    gdf = geopandas dataframe that has already been filtered for sensors within
        a geographic area using analyze.maps.sensor_df_to_geo()
    start_date, end_date = datetime.datetime date
    """
    pass


def sensorid_to_df(sensor_id):
    """Return dataframe of current sensor data from sensor with id = sensor_id"""
    print(sensor_id)
    dict_ = Sensor(int(sensor_id)).as_dict()
    row_dict = {}
    for channel in dict_:
        suffix = {'parent': '_1', 'child': '_2'}[channel]
        for k1 in dict_[channel]:
            for k2 in dict_[channel][k1]:
                row_dict[k2+suffix] = [dict_[channel][k1][k2]]
    # Add created datetime column
    created_unix = dict_['parent']['diagnostic']['created']
    return (pd.DataFrame.from_dict(row_dict)
          .assign(created_date=datetime.utcfromtimestamp(created_unix)))


def load_current_sensor_data(update_lookup=True):
    """Return dataframe of current sensor data."""
    df = df_sensors()
    df = filter_data(df)
    # Update sensor location lookup table
    if update_lookup:
        update_loc_lookup(df)
    return df


def update_loc_lookup(df, output=False):
    """Update the location lookup table for sensor id's; return lookup if output=True."""
    loc_cols = ['id', 'lat', 'lon', 'date']
    try:
        loc_lookup = pd.read_csv(PATHS.data.lookup_location)
    except FileNotFoundError:
        loc_lookup = pd.DataFrame(columns=loc_cols)
    # Update lookup
    today = datetime.today().date().strftime('%Y-%m-%d')
    loc_lookup = (loc_lookup.merge(df
                                   .reset_index()
                                   .filter(loc_cols, axis=1),
                                   how='outer',
                                   on=['id', 'lat', 'lon'])
                  .fillna({'date': today}))
    loc_lookup.to_csv(PATHS.data.lookup_location, index=False)
    if output:
        return loc_lookup


def parse_json(json_):
    dict_ = json.loads(json_)
    return


if __name__ == "__main__":
    sensor_df = load_current_sensor_data()
    sensor_df2 = pd.concat([sensorid_to_df(id) for id in sensor_df.index[:21]])
    # Single sensor
    se = Sensor(int(sensor_df.index[0]))
    print(se)
    print(se.parent)
    print(se.child)
    print(se.parent.as_flat_dict())
    se.get_field(3)
    se.get_field(4)
    print(se.thingspeak_data.keys())
    df = se.parent.get_historical(weeks_to_get=1, thingspeak_field='primary')
    df2 = se.child.get_historical(weeks_to_get=1, thingspeak_field='p')
    df.created_at.groupby(df["created_at"].dt.date).count().plot(kind="bar")

    se2 = [Sensor(id) for id in sensor_df.index[:2]]
    se2 = []
    cols_to_keep = ['UptimeMinutes', 'ADC', 'Temperature_F', 'Humidity_%', 'PM2.5 (CF=ATM) ug/m3']
    dfs = [(se
            .parent
            .get_historical(weeks_to_get=1, thingspeak_field='primary')
            .assign(sensor_id=se.identifier, channel='parent')
            .filter(cols_to_keep, axis=1)) for se in se2]

    se.get_data()
    print(df.head())
    print(df.tail())
