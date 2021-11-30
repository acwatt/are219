#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
# Third-party Imports
# Local Imports
import acwatt_syp_code.analyze.maps as am
import acwatt_syp_code.build.purpleair_download as pad
from acwatt_syp_code.utils.config import PATHS

if __name__ == "__main__":
    # Get available sensor locations from  from purpleair.network.SensorList API wrapper
    sensor_df = pad.load_current_sensor_data()
    # Make sensor plots
    # am.make_all_sensor_maps(sensor_df)
    # Save sensor dataframe
    sensor_gdf, base_gdf = am.sensor_df_to_geo(sensor_df, 'us')
    (sensor_gdf
     .reset_index()
     .to_csv(PATHS.data.purpleair / 'location_us_pan_request_2021-11-29_geocoded.csv',
             index=False))

    # Start downloading PA sensor data

    pad.dl_in_geo_area(sensor_gdf, start_date, num_weeks=10)
