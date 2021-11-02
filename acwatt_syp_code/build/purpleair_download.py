#!/usr/bin/env python

"""Functions to download purple air data via their API"""

# Built-in Imports
# Third-party Imports
from purpleair.network import SensorList
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
    # Other sensor filters include 'outside', 'all', 'family', and 'no_child'
    df = p.to_dataframe(sensor_filter='useful',
                        channel='parent')
    print(len(df))  # 16902
    return df


def download_pm25(sensor_list):
    """Save dataframe of PM 2.5 data from all valid sensors."""
    for s in sensor_list:
        pass



if __name__ == "__main__":
    sensor_list = list_sensors()
