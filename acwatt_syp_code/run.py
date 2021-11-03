#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
# Third-party Imports
# Local Imports
import analyze.maps as am
import build.purpleair_download as pad

if __name__ == "__main__":
    sensor_df = pad.load_sensor_data()
    am.make_all_sensor_maps(sensor_df)
