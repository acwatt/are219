#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import logging
import datetime as dt
import pandas as pd
import numpy as np
import os
import io
# Third-party Imports
import boto3
from botocore.exceptions import ClientError
# Local Imports
from ..utils.config import PATHS, AWS

logger = logging.getLogger(__name__)


def download_file(bucket_name, bucket_filepath):
    """Return a pandas dataframe of a CSV from an S3 bucket

    :param bucket_filepath: File to download
    :param bucket_name: Bucket to upload to
    """

    # Upload the file
    s3_client = boto3.client('s3',
                             region_name=AWS.region,
                             aws_access_key_id=AWS.access_key,
                             aws_secret_access_key=AWS.secret_key)
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=bucket_filepath)
        df = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8', header=[0,1])
        return df
        # response = s3_client.get_object(Bucket=bucket, Key=bucket_file)
        # response = s3_client.upload_file(file_path, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False


def minmax(series):
    return max(series)-min(series)


def correction_factor(pm, humidity):
    """Return PM2.5 corrected values for matching PurpleAir to EPA 88101 monitors.
    
    See docs/purpleair/purpleair_specs.md for more notes.
    humidity is percentage, so much devide by 100
    """
    if pm <= 343:
        return 0.52*pm - 0.086*humidity/100 + 5.75
    else:
        return 0.46*pm + (3.93e-4)*(pm**2) + 2.97


def flag_large_diff(pm_avg, pm_diff):
    """Return 1 if diff is both >= 5ug/m^3 and >= 70% of avg, else 0"""
    return int( (pm_diff >= 5) and (pm_diff/pm_avg >= 0.7) )


def make_quarter(date: str):
    year, month, day = date.split("-")
    quarter = int(np.ceil(int(month)/3))
    return quarter


def transform_pa_df(df):
    # Rename 6 columns to keep
    cols = [' '.join(col).strip() for col in df.columns.values]
    replace_list = ['created_at', 'channel', 'sensor_id', 'Humidity', 'PM2.5 (CF=1)', 'Temperature']
    cols = [col.split(' ')[0].lower() if any(search in col for search in replace_list) else col for col in cols]
    df.columns = cols
    # Drop unused channels
    keep_cols = ['created_at', 'channel', 'sensor_id', 'humidity', 'pm2.5', 'temperature']
    df = df[keep_cols]
    # Convert long to wide on channels, calculate mean PM2.5 and difference between channels
    df2 = df.groupby('created_at').agg({'sensor_id': 'first',
                                        'pm2.5': ['mean', minmax],
                                        'humidity': 'mean',
                                        'temperature': 'mean'}).reset_index()
    df2.columns = ['created_at', 'sensor_id', 'pm2.5_avg', 'pm2.5_diff', 'humidity', 'temperature']
    # Flag readings that are too different (ref: EPA, see notes at bottom)
    df2['large_diff'] = df2.apply(lambda row: flag_large_diff(row['pm2.5_avg'], row['pm2.5_diff']), axis=1)
    # Create date and time columns that match EPA data
    df2['date_local'] = df2['created_at'].str.split("T").str[0]
    df2['time_local'] = df2['created_at'].str.split("T").str[1].str.split(":00-").str[0]
    df_pa['year'] = df_pa['date_local'].str.split("-").str[0]
    df_pa['quarter'] = df2.apply(lambda row: make_quarter(row['date_local']), axis=1)
    # Add PA-EPA correction factor
    df2['pm2.5_corrected'] = df2.apply(lambda row: correction_factor(row['pm2.5_avg'], row['humidity']), axis=1)
    return df2


threshold = 5  # miles
bucket = 'purpleair-data'
power = 1  # IDW power

# For each EPA site-county in list
lookup_dir = PATHS.data.tables / 'epa_pa_lookups'
county, site = "037", "4004"  # start with one site
# Load EPA data
df_epa = pd.read_csv(PATHS.data.epa_pm25 / f"county-{county}_site-{site}_hourly.csv")
df_epa['year'] = df_epa['date_local'].str.split("-").str[0]
# Load sensor list for this site
sensor_list = pd.read_csv(lookup_dir / f'county-{county}_site-{site}_pa-list.csv')
sensor_list = sensor_list.query(f"dist_mile < {threshold}").sort_values('dist_mile')
# For each sensor in list, download CSV from S3 to get PM2.5 values
for sensor_id, dist in zip(sensor_list['sensor_index'], sensor_list['dist_mile']):
    # Downlaod the file to dataframe
    bucket_file = f'{sensor_id:07d}.csv'
    df_pa = download_file(bucket, bucket_file)
    # Transform the dataframe to get PM2.5 and humidity
    df_pa = transform_pa_df(df_pa)
    df_pa['weight_raw'] = 1 / dist**power

    print(df_pa.groupby('year').count().sort_values('pm2.5_corrected'))
    year = df_pa.groupby('year').count().sort_values('pm2.5_corrected').head(1).reset_index()['year'][0]
    q1 = f"date_local >= '{year}-01-01' and date_local <= '{year}-12-31'"
    ax = (df_epa
          .query(q1)
          .groupby('time_local').mean().reset_index()
          .plot(x='time_local', y='sample_measurement',
                label='EPA PM2.5',
                title=f"PM2.5 EPA-PA comparison for sensor {sensor_id} in {year}"))
    (df_pa
     .query(q1)
     .groupby('time_local').mean().reset_index()
     .plot(x='time_local', y='pm2.5_avg', ax=ax, label='PA PM2.5 Raw'))
    (df_pa
     .query(q1)
     .groupby('time_local').mean().reset_index()
     .plot(x='time_local', y='pm2.5_corrected', ax=ax, label='PA PM2.5 Corrected'))



