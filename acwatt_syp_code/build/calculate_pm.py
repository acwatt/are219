#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import logging
import datetime as dt
import pandas as pd
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
    return df2
    # Match times between PA and EPA?

threshold = 5  # miles
bucket = 'purpleair-data'

# For each EPA site-county in list
lookup_dir = PATHS.data.tables / 'epa_pa_lookups'
county, site = "037", "4004"  # start with one site
# Load sensor list for this site
sensor_list = pd.read_csv(lookup_dir / f'county-{county}_site-{site}_pa-list.csv')
sensor_list = sensor_list.query(f"dist_mile < {threshold}")
# For each sensor in list, download CSV from S3 to get PM2.5 values
sensor_id, dist = 489, 4.932198
# Downlaod the file to dataframe
bucket_file = f'{sensor_id:07d}.csv'
df_pa = download_file(bucket, bucket_file)
# Transform the dataframe to get PM2.5 and humidity
df_pa = transform_pa_df(df_pa)
# Load EPA data
df_epa = pd.read_csv(PATHS.data.epa_pm25 / f"county-{county}_site-{site}_hourly.csv")




