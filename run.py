#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
# Third-party Imports
# Local Imports
import acwatt_syp_code.analyze.maps as am
import acwatt_syp_code.build.purpleair_download as pad
from acwatt_syp_code.utils.config import PATHS

if __name__ == "__main__":
    sensor_df = pad.load_current_sensor_data()
    # sensor_gdf, base_gdf = am.sensor_df_to_geo(sensor_df, 'california')

    # pad.download_in_geo_area(sensor_gdf, )
    am.make_all_sensor_maps(sensor_df)
