#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import pandas as pd
# Third-party Imports
# Local Imports
import acwatt_syp_code.analyze.maps as am
import acwatt_syp_code.build.purpleair_download as pad
from acwatt_syp_code.utils.config import PATHS
from acwatt_syp_code.build.aws import lambda_services

if __name__ == "__main__":
    lambda_services.save_pa_data_to_s3()
    # Get available sensor locations from  from purpleair.network.SensorList API wrapper
    # sensor_df = pad.load_current_sensor_data()
    # Get available sensor locations from thingsspeak API directly
    sensors = [25999] #, 22751]
    df_pa = pad.pa_request(sensors[0])
    df_ts = pad.ts_example()
    dfs = [pad.dl_sensor_weeks(id_, date_start='2021-12-25') for id_ in sensors]
    df_total = pd.concat(dfs).sort_values('created_at')
    df_total['datetime'] = pd.to_datetime(df_total['created_at'])
    df_total.index = df_total['datetime']
    df_hourly = df_total.resample('H').mean()
    dfs = [pad.dl_sensor_weeks(id_, date_start='2021-12-25', average=60) for id_ in sensors]
    df_total2 = pd.concat(dfs).sort_values('created_at')
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
