#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import logging
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
# Third-party Imports
import boto3
from botocore.exceptions import ClientError
# Local Imports
from ..utils.config import PATHS, AWS

logger = logging.getLogger(__name__)


def make_hourly_avg_plots(df_pa, df_epa, sensor_id):
    """Make a plot comparing hourly epa data to a single PA sensor's data over the year.

    Pick the year that the PA sensor has the most data for and the EPA
    """
    year = df_pa.groupby('year').count().sort_values('pm2.5_corrected').head(1).reset_index()['year'][0]
    if year == "2022":
        year = "2021"
    q1 = f"date_local >= '{year}-01-01' and date_local <= '{year}-12-31'"
    # Plot EPA data
    ax = (df_epa
          .query(q1)
          .groupby('time_local').mean().reset_index()
          .plot(x='time_local', y='sample_measurement',
                label='EPA PM2.5',
                title=f"PM2.5 EPA-PA comparison for sensor {sensor_id} in {year}"))
    # Plot uncorrected PA data for this sensor
    (df_pa
     .query(q1)
     .groupby('time_local').mean().reset_index()
     .plot(x='time_local', y='pm2.5_avg', ax=ax, label='PA PM2.5 Raw'))
    # Plot corrected EPA data for this sensor
    (df_pa
     .query(q1)
     .groupby('time_local').mean().reset_index()
     .plot(x='time_local', y='pm2.5_corrected', ax=ax, label='PA PM2.5 Corrected'))
    plt.show()


def plot_epa_vs_pa(df_epa, county, site, color_category = 'hour of day'):
    if color_category == 'hour of day':
        df_epa[color_category] = df_epa['time_local'].str.split(':').str[0].astype(int)
        color_map = 'twilight_shifted'
    else:
        df_epa[color_category] = df_epa[color_category].astype(int)
        color_map = 'Set1'
    plt.figure()
    ax = df_epa.plot.scatter(x='pm2.5_pa', y='pm2.5_epa', c=color_category, colormap=color_map,
                             xlabel='PurpleAir Inv Dist Weighted Avg PM2.5',
                             ylabel='EPA PM2.5',
                             title=f"EPA vs PurpleAir IDW Avg PM2.5 for site {county}-{site}",
                             figsize=(10, 8), s=12, alpha=0.8)
    max_pm = df_epa['pm2.5_epa'].max()
    ax.plot([0, max_pm], [0, max_pm], color='red')
    plt.tight_layout()
    p = PATHS.output / 'figures' / 'epa_vs_pa' / f'site-{county}-{site}_epa-pa-hourly-plot.png'
    plt.savefig(p, dpi=200)
    plt.close()


def plot_epa_missing_vs_pa(df_epa, county, site, bins=10):
    df_epa['EPA missing'] = df_epa['pm2.5_epa'].isna()
    plt.figure()
    sns.set(rc={'figure.figsize': (10, 8)})
    ax = sns.regplot(x='pm2.5_pa', y='EPA missing', data=df_epa, logistic=True)
    ax.set_xlabel('PurpleAir Inv Dist Weighted Avg PM2.5', fontsize=20)
    ax.set_ylabel('EPA PM2.5 is Missing', fontsize=20)
    ax.set_title(f"EPA missing hour vs PurpleAir IDW PM2.5 for site {county}-{site}")
    plt.tight_layout()
    p = PATHS.output / 'figures' / 'epa_vs_pa' / f'site-{county}-{site}_epa-pa-missing-plot.png'
    plt.savefig(p, dpi=200)
    plt.close()


def density_epa_missing_vs_pa(df_epa, county, site):
    fontsize_ = 12
    df_epa['EPA missing'] = df_epa['pm2.5_epa'].isna()
    df_mis = df_epa.query("`EPA missing` and `pm2.5_pa` < 50")
    df_nomis = df_epa.query("not `EPA missing` and `pm2.5_pa` < 50")
    plt.figure(figsize=(7, 4))
    ax = df_mis['pm2.5_pa'].plot.density(label='Missing EPA Hours')
    df_nomis['pm2.5_pa'].plot.density(ax=ax, label='Nonmissing EPA Hours')
    ax.set_xlabel('PurpleAir Inv Dist Weighted Avg PM2.5', fontsize=fontsize_)
    ax.set_ylabel('Hour Observation Density', fontsize=fontsize_)
    ax.set_title(f"EPA missing and non-missing hours' density on PurpleAir IDW PM2.5 for site {county}-{site}         ", fontsize=fontsize_-1)
    ax.set_xlim([0, 50])
    plt.legend(fontsize=fontsize_)
    plt.tight_layout()
    p = PATHS.output / 'figures' / 'epa_vs_pa' / f'site-{county}-{site}_epa-pa-missing-density.png'
    plt.savefig(p, dpi=200)
    plt.close()


def load_epa(county: str, site: str):
    df_epa = pd.read_csv(PATHS.data.epa_pm25 / f"county-{county}_site-{site}_hourly.csv")
    df_epa['year'] = df_epa['date_local'].str.split("-").str[0]
    df_epa['quarter'] = df_epa.apply(lambda row: make_quarter(row['date_local']), axis=1)
    df_epa = df_epa.rename(columns={'sample_measurement': 'pm2.5_epa'})
    return df_epa


def save_combined_file(df_epa, county, site):
    keep = ['state_code', 'county_code', 'site_number', 'year', 'quarter', 'date_local', 'time_local', 'pm2.5_epa', 'pm2.5_pa', 'sample_duration', 'qualifier']
    df_epa2 = df_epa[keep]
    p = PATHS.data.root / 'combined_epa_pa' / f"county-{county}_site-{site}_combined-epa-pa.csv"
    df_epa2.to_csv(p, index=False)


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
        print(f'Unable to retrieve S3 object {bucket_filepath}')
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
    df2['year'] = df2['date_local'].str.split("-").str[0]
    df2['quarter'] = df2.apply(lambda row: make_quarter(row['date_local']), axis=1)
    # Add PA-EPA correction factor
    df2['pm2.5_corrected'] = df2.apply(lambda row: correction_factor(row['pm2.5_avg'], row['humidity']), axis=1)
    return df2


def concat_sensors(sensor_list: pd.DataFrame):
    df_list = []
    for sensor_id, dist in zip(sensor_list['sensor_index'], sensor_list['dist_mile']):
        print(f'Starting sensor {sensor_id}')
        # Downlaod the file to dataframe
        bucket_file = f'{sensor_id:07d}.csv'
        df_pa = download_file(bucket, bucket_file)
        if df_pa is False:
            continue  # Skip this sensor if there is no file in the S3 for it
        # Transform the dataframe to get PM2.5 and humidity
        df_pa = transform_pa_df(df_pa)
        df_pa['weight_raw'] = 1 / dist ** power
        # make_hourly_avg_plots(df_pa, df_epa, sensor_id)
        df_list.append(df_pa)

    if not df_list:
        return False
    df = pd.concat(df_list, ignore_index=True).sort_values(['created_at', 'sensor_id'])
    df = df.query('large_diff == 0')  # remove any sensor-hours that have large channel discrepancies
    return pd.concat(df_list, ignore_index=True).sort_values(['created_at', 'sensor_id'])


def average_sensors(df):
    """Return df with one weighted average PM2.5 for each hour.

    Each hour is a weighted average of the PA sensors that have that hour valid.
    """
    def weighted_avg(x):  # input is a group's dataframe
        pm_wavg = {'pm2.5_pa': (x['weight_raw'] * x['pm2.5_corrected']).sum() / x['weight_raw'].sum()}
        return pd.Series(pm_wavg, index=['pm2.5_pa'])

    df2 = df.groupby(['date_local', 'time_local']).apply(weighted_avg).reset_index()
    return df2


def add_pa_pm(df_epa, county, site):
    # Load sensor list for this site
    sensor_list = pd.read_csv(lookup_dir / f'county-{county}_site-{site}_pa-list.csv')
    sensor_list = sensor_list.query(f"dist_mile < {threshold}").sort_values('dist_mile')
    # For each sensor in list, download CSV from S3 to get PM2.5 values
    df_pa = concat_sensors(sensor_list)
    if df_pa is False:
        return False
    # Combine PA sensors to get hourly weighted average PM2.5
    df_pa2 = average_sensors(df_pa)
    # Merge with EPA data
    df_epa2 = df_epa.merge(df_pa2, on=['date_local', 'time_local'],
                           suffixes=("_epa", "_pa"), how='left')
    return df_epa2


threshold = 5  # miles
bucket = 'purpleair-data'
power = 1  # IDW power
lookup_dir = PATHS.data.tables / 'epa_pa_lookups'

# cs_list = [("037", "4004"), ("031", "1004"), ("057", "0005")]
dtypes = {"county": str, "site": str}
aqs_tbl = (pd.read_csv(lookup_dir / 'aqs_monitors_to_pa_sensors.csv', dtype=dtypes))
aqs_tbl['download_order'] = aqs_tbl['county'] + '-' + aqs_tbl['site']
aqs_tbl = aqs_tbl.replace({'download_order': {"037-4004": "000-0001",
                                              "031-1004": "000-0002",
                                              "057-0005": "000-0003"}})
aqs_tbl = (aqs_tbl
           .sort_values('download_order')[['county', 'site']]
           .drop_duplicates()
           .values.tolist())
# For each EPA site-county in list
county, site = "037", "4004"
for county, site in aqs_tbl:  # cs_list
    p = PATHS.data.root / 'combined_epa_pa' / f"county-{county}_site-{site}_combined-epa-pa.csv"
    if p.exists():
        df_epa = pd.read_csv(p)
    else:
        print(f'Starting site {county}-{site}')
        # Load EPA data
        df_epa = load_epa(county, site)

        # Calculate hourly weighted average PurpleAir PM2.5 for this site
        df_epa = add_pa_pm(df_epa, county, site)
        if df_epa is False:
            continue
        save_combined_file(df_epa, county, site)
    plot_epa_vs_pa(df_epa, county, site, color_category='year')
    plot_epa_missing_vs_pa(df_epa, county, site)
    try:
        density_epa_missing_vs_pa(df_epa, county, site)
    except ValueError:
        print('No PurpleAir data overlaps with missing EPA data.')


"""NOTES:
Steps for PA correction to match EPA monitors from:
https://cfpub.epa.gov/si/si_public_file_download.cfm?p_download_id=540979&Lab=CEMM

Updated correction equation from EPA presentation. See docs/purpleair/purpleair_specs.md 
"""