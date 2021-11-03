#!/usr/bin/env python

"""Functions to download purple air data via their API"""

# Built-in Imports
# Third-party Imports
from purpleair.network import SensorList, Sensor
# Local Imports


READ_KEY = '5498FF4F-1642-11EC-BAD6-42010A800017'
WRITE_KEY = '5499CF6C-1642-11EC-BAD6-42010A800017'

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


def list_sensors():
    """Return list of sensors that have valid data."""
    p = SensorList()  # Initialized 22,877 sensors!
    # Other sensor filters include 'outside', 'all', 'useful', 'family', and 'no_child'
    df = p.to_dataframe(sensor_filter='all',
                        channel='parent')
    return df


def filter_data(df):
    df = (df.query('location_type == "outside"')
          .query('downgraded == False')
          .query('flagged == False')
          )
    return df


def download_pm25(sensor_list):
    """Save dataframe of PM 2.5 data from all valid sensors."""
    for s in sensor_list:
        pass


def get_data_from_sensor(sensor_id):
    sensor = Sensor(sensor_id)
    df = sensor.parent.get_historical(weeks_to_get=1,
                                  thingspeak_field='secondary')
    return df


def load_sensor_data():
    sensor_df = list_sensors()
    sensor_df = filter_data(sensor_df)
    # Single sensor

    se = Sensor(int(sensor_df.index[0]))
    print(se)
    print(se.parent)
    print(se.child)
    print(se.parent.as_flat_dict())
    se.get_field(3)
    se.get_field(4)
    print(se.thingspeak_data.keys())
    df = se.parent.get_historical(weeks_to_get=1,
                                  thingspeak_field='secondary')

    print(df.head())
    print(df.tail())
    return sensor_df


