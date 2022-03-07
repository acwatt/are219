#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import logging
import datetime as dt

import botocore.exceptions
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns
import statsmodels.api as sm
from statsmodels.iolib.summary2 import summary_col
from stargazer.stargazer import Stargazer, LineLocation
import time
import os
import io
# Third-party Imports
import boto3
from botocore.exceptions import ClientError
# Local Imports
from ..utils.config import PATHS, AWS

logger = logging.getLogger(__name__)
DTYPES = {"county_code": str, "county": str, "County Code": str, "State Code": str,
          "site_number": str, "site": str, "Site Number": str, "Site Num": str,
          "Qualifier Type Code": str}


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
    fig = plt.figure()
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
    plt.close(fig)


def plot_epa_missing_vs_pa(df_epa, county, site, bins=10):
    df_epa['EPA missing'] = df_epa['pm2.5_epa'].isna()
    fig = plt.figure()
    sns.set(rc={'figure.figsize': (10, 8)})
    ax = sns.regplot(x='pm2.5_pa', y='EPA missing', data=df_epa, logistic=True)
    ax.set_xlabel('PurpleAir Inv Dist Weighted Avg PM2.5', fontsize=20)
    ax.set_ylabel('EPA PM2.5 is Missing', fontsize=20)
    ax.set_title(f"EPA missing hour vs PurpleAir IDW PM2.5 for site {county}-{site}")
    plt.tight_layout()
    p = PATHS.output / 'figures' / 'epa_vs_pa' / f'site-{county}-{site}_epa-pa-missing-plot.png'
    plt.savefig(p, dpi=200)
    plt.close(fig)


def density_epa_missing_vs_pa(df_epa, county, site):
    fontsize_ = 12
    max_percentile_to_plot = 98
    df_epa['EPA missing'] = df_epa['pm2.5_epa'].isna()
    # df_mis = df_epa.query("`EPA missing` and `pm2.5_pa` < 50")
    # df_nomis = df_epa.query("not `EPA missing` and `pm2.5_pa` < 50")
    df_mis = df_epa.query("`EPA missing`")
    df_nomis = df_epa.query("not `EPA missing`")
    fig = plt.figure(figsize=(7, 4))
    ax = df_mis['pm2.5_pa'].plot.density(label='Missing')
    df_nomis['pm2.5_pa'].plot.density(ax=ax, label='Reported')
    ax.set_xlabel('PurpleAir Inv Dist Weighted Avg PM2.5', fontsize=fontsize_)
    ax.set_ylabel('Hour Observation Density', fontsize=fontsize_)
    ax.set_title(f"Kernal Density of PurpleAir PM2.5 for Hours where\nNAAQS Monitor Measurements are Reported vs Missing (site {county}-{site})         ", fontsize=fontsize_-1)
    max_ = np.nanpercentile(df_epa['pm2.5_pa'], max_percentile_to_plot)
    min_ = -1*max_/8
    ax.set_xlim([min_, max_])
    plt.legend(fontsize=fontsize_)
    plt.tight_layout()
    p = PATHS.output / 'figures' / 'epa_vs_pa' / f'site-{county}-{site}_epa-pa-missing-density.png'
    plt.savefig(p, dpi=200)
    plt.close(fig)


def plot_pa_coverage(df_epa, county, site):
    fontsize_ = 12
    df_epa['PA not missing'] = df_epa['pm2.5_pa'].isna().apply(lambda x: not x)
    daily = df_epa.groupby('date_local').sum().reset_index()
    daily['date'] = pd.to_datetime(daily['date_local'])
    fig = plt.figure(figsize=(5, 5))
    ax = daily.plot.scatter(y='PA not missing', x='date', s=10)
    ax.set_xlabel('Date of PM2.5 measurement', fontsize=fontsize_)
    ax.set_ylabel('# of hours in the day with PurpleAir Coverage', fontsize=fontsize_)
    ax.set_title(f"Hours per day with PurpleAir Coverage for site {county}-{site}", fontsize=fontsize_-1)
    ax.set_xlim([dt.datetime.strptime('2016', '%Y'), dt.datetime.strptime('2022', '%Y')])
    # ax.get_legend().remove()
    plt.tight_layout()
    p = PATHS.output / 'figures' / 'epa_vs_pa' / f'site-{county}-{site}_pa-daily-covereage.png'
    plt.savefig(p, dpi=200)
    plt.close(fig)


def site_plots(county, site):
    p = PATHS.data.root / 'combined_epa_pa' / f"county-{county}_site-{site}_combined-epa-pa.csv"
    try:
        df_epa = pd.read_csv(p)
    except FileNotFoundError:
        print(f'No file {p.name}. Skipping plots for site {county}-{site}')
        return
    plot_epa_vs_pa(df_epa, county, site, color_category='year')
    # plot_epa_missing_vs_pa(df_epa, county, site)
    try:
        density_epa_missing_vs_pa(df_epa, county, site)
    except ValueError:
        print('No PurpleAir data overlaps with missing EPA data.')
    plot_pa_coverage(df_epa, county, site)


def load_epa(county: str, site: str):
    logger.info(f"Loading EPA data")
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
    # try:
    #     obj = s3_client.get_object(Bucket=bucket_name, Key=bucket_filepath)
    #     df = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8', header=[0,1])
    #     return df
    #     # response = s3_client.get_object(Bucket=bucket, Key=bucket_file)
    #     # response = s3_client.upload_file(file_path, bucket, object_name)
    # except ClientError as e:
    #     logger.warning(f'\nUnable to retrieve S3 object {bucket_filepath}. It was probably privat when you tried to download it originally.')
    #     logging.error(e)
    #     return False
    # except botocore.exceptions.ResponseStreamingError:
    #     pass

    sleepy_time = 1
    func_return = None
    while sleepy_time < 33 and func_return is None:
        try:
            obj = s3_client.get_object(Bucket=bucket_name, Key=bucket_filepath)
            df = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8', header=[0, 1])
            return df
        except ClientError as error:
            print()
            logging.error(error)
            logger.warning(f'Unable to retrieve S3 object {bucket_filepath}. It was probably privat when you tried to download it originally.')
            return None
        except botocore.exceptions.ResponseStreamingError as error:
            logger.info(f"Sleeping for {sleepy_time} to give AWS time to "
                        f"connect resources.")
            time.sleep(sleepy_time)
            sleepy_time = sleepy_time*2
    logger.warning(f"Reached max retry time to download S3 object {bucket_filepath}.\nMoving on.")
    return None




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


def concat_sensors(sensor_list: pd.DataFrame, power=1):  # IDW power
    logger.info(f"Loading {len(sensor_list)} PurpleAir sensors.")
    df_list = []
    for sensor_id, dist in zip(sensor_list['sensor_index'], sensor_list['dist_mile']):
        print("*", end='')
        # Downlaod the file to dataframe
        bucket_file = f'{sensor_id:07d}.csv'
        df_pa = download_file(AWS.bucket_name, bucket_file)
        if df_pa is None:
            continue  # Skip this sensor if there is no file in the S3 for it
        # Transform the dataframe to get PM2.5 and humidity
        df_pa = transform_pa_df(df_pa)
        df_pa['weight_raw'] = 1 / dist ** power
        # make_hourly_avg_plots(df_pa, df_epa, sensor_id)
        df_list.append(df_pa)

    print()
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


def filter_sensors(sensor_list, threshold, min_sensors=10):
    if len(sensor_list.query(f"dist_mile < {threshold}")) >= min_sensors:
        return sensor_list.sort_values('dist_mile').query(f"dist_mile < {threshold}")
    else:
        return sensor_list.sort_values('dist_mile').iloc[0:min_sensors]


def add_pa_pm(df_epa, county, site, threshold=5, power=1, min_sensors=10):
    logger.info(f"Adding PurpleAir PM data to EPA data")
    logger.info(f"Using radius of {threshold}, IDW exponent of {power}, and min # of sensors {min_sensors}.")
    lookup_dir = PATHS.data.tables / 'epa_pa_lookups'
    # Load sensor list for this site
    sensor_list = pd.read_csv(lookup_dir / f'county-{county}_site-{site}_pa-list.csv')
    sensor_list = filter_sensors(sensor_list, threshold, min_sensors=min_sensors)
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


def load_15_sites():
    logger.info("Loading list of county-site number pairs for EPA monitors.")
    lookup_dir = PATHS.data.tables / 'epa_pa_lookups'
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
    return aqs_tbl


def load_combined(site_dict):
    county, site = site_dict['county'], site_dict['site']
    p = PATHS.data.root / 'combined_epa_pa' / f"county-{county}_site-{site}_combined-epa-pa.csv"
    return pd.read_csv(p, dtype=DTYPES)


def load_qualifiers():
    p = PATHS.data.tables / 'aqs_qualifiers.csv'
    return pd.read_csv(p, converters={'Qualifier Type Code' : str})[['Qualifier Code', 'Qualifier Type Code']]


def test_15_sites(run_all=False):
    threshold = 5  # miles
    idw_power = 1  # Inv Distance Weighting Denominator Exponent
    min_sensors = 10  # min # of PA sensors to grab near EPA monitor
    aqs_tbl = load_15_sites()
    # For each EPA site-county in list
    county, site = '031', '0004'  # for line-by-line debugging
    for county, site in aqs_tbl:
        p = PATHS.data.root / 'combined_epa_pa' / f"county-{county}_site-{site}_combined-epa-pa.csv"
        if p.exists() and not run_all:
            df_epa = pd.read_csv(p)
        else:
            logger.info(f'{county}-{site}: Starting PA weighted average' + '='*30)
            # Load EPA data
            df_epa = load_epa(county, site)
            # Calculate hourly weighted average PurpleAir PM2.5 for this site
            df_epa = add_pa_pm(df_epa, county, site,
                               threshold=threshold, power=idw_power,
                               min_sensors=min_sensors)
            if df_epa is False:
                logger.warning(f"Was unable to calculate weighted average for site {county}-{site}.")
                continue
            save_combined_file(df_epa, county, site)


def make_plots_15_sites():
    aqs_tbl = load_15_sites()
    # For each EPA site-county in list
    for county, site in aqs_tbl:  # cs_list
        print(f'Starting plots for {county}-{site}.')
        site_plots(county, site)


def add_exceptional_indicator(df):
    df_l = df.copy(deep=True)
    df_r = load_qualifiers()
    df_l['Qualifier Code'] = df_l.qualifier.str.split(' ', expand=True)[0]
    df_l = df_l.merge(df_r, on='Qualifier Code', how='left')
    exception_list = ['REQEXC']  # 'NULL', 'NULL QC'
    df['drop_qualifier'] = df_l['Qualifier Type Code'].isin(exception_list)
    return df


def fill_in_missing_with_idw(df):
    df['pm2.5_epa.idw.pa'] = np.where(df['pm2.5_epa'].isna(), df['pm2.5_pa'], df['pm2.5_epa'])
    return df


def fill_in_missing_with_OLS(df, site_dict, alpha=0.05):
    # Remove missing values from y and x for regression
    df1 = df[~df['pm2.5_epa'].isna() & ~df['pm2.5_pa'].isna()]
    y = df1['pm2.5_epa']
    x = df1['pm2.5_pa']
    # Run regression
    model1 = sm.OLS(y, x).fit()
    # Generate predicted EPA values from full set of weighted avereage Purple Air values
    epa_hat = model1.predict(df['pm2.5_pa'])
    # Replace EPA missing values with OLS prediction (nc = No Constant)
    df['pm2.5_epa.olsnc.pa'] = np.where(df['pm2.5_epa'].isna(), epa_hat, df['pm2.5_epa'])
    df['errors_nc'] = df['pm2.5_epa'] - epa_hat

    # Do the same using OLS with a constant (yc = Yes Constant)
    x2 = sm.add_constant(x)
    model2 = sm.OLS(y, x2).fit()

    # Push predictions into missing EPA slots (add constant to full PurpleAir column to predict)
    predictions = model2.get_prediction(sm.add_constant(df['pm2.5_pa']))
    frame = predictions.summary_frame(alpha=alpha)
    epa_hat2 = frame['mean']
    df['pm2.5_epa.olsyc.pa'] = np.where(df['pm2.5_epa'].isna(), epa_hat2, df['pm2.5_epa'])
    df['errors_yc'] = df['pm2.5_epa'] - epa_hat2
    # Get prediction confidence interval upper and lower bounds for each observations
    df['upper.yc'] = frame.obs_ci_upper  # Full set of upper bounds
    df['lower.yc'] = frame.obs_ci_lower  # Full set of lower bounds
    # Create two more combined sets of EPA PM, filling in upper and lower predictions
    df['pm2.5_epa.olsyc.pa.upper'] = np.where(df['pm2.5_epa'].isna(), df['upper.yc'], df['pm2.5_epa'])
    df['pm2.5_epa.olsyc.pa.lower'] = np.where(df['pm2.5_epa'].isna(), df['lower.yc'], df['pm2.5_epa'])

    # Save the regression summaries
    c_s = f'{site_dict["county"]}-{site_dict["site"]}'
    stargazer = Stargazer([model1, model2])
    stargazer.title(f'{c_s} NAAQS Monitor PM2.5 on Weighted Average PurpleAir PM2.5')
    # stargazer.custom_columns(['No Intercept', 'Intercept'], [1, 1])
    # stargazer.show_model_numbers(False)
    stargazer.show_degrees_of_freedom(False)
    stargazer.rename_covariates({'pm2.5_pa': 'PurpleAir IDW Average'})
    stargazer.dependent_variable_name(f'Reported NAAQS Monitor PM2.5')
    stargazer.add_line('Preferred', ['No', 'Yes'], LineLocation.FOOTER_TOP)
    stargazer.table_label = f'tab:reg_{c_s}'
    table = stargazer.render_latex()
    p = PATHS.output / 'tables' / f'epa_OLS_idw_pa_site-{c_s}.tex'
    with open(p, "w") as file1:
        # Writing data to a file
        file1.write(table)
    return df


def valid_daily(x: pd.Series):
    """NAAQS design value daily average validity criterion."""
    return x.count() >= 0.75*24


def valid_quarter(df: pd.DataFrame):
    """NAAQS design value quarterly validity criterion, to be used with groupby.apply()

    Input must have multi index of year, quarter, and should be a "valid" column
    with boolean values.
    """
    result = {f"{col.split('_')[0]}_valid_quarter": df[col].sum() >= df['min_days'].mean() for col in df.columns if 'valid_daily' in col}
    return pd.Series(result)


def add_quarterly_valid_indicators(df: pd.DataFrame):
    """Return quarterly validation indicators from daily dataframe.

    From EPA compleness criteria: every quarter must have 75% complete, but they
    give the # of minimum days for each quarter as {1: 68, 2: 68, 3: 69, 4: 69}.
    """
    df1 = df.copy(deep=True)
    valid_days_lookup = {1: 68, 2: 68, 3: 69, 4: 69}
    df1['min_days'] = df.quarter.map(valid_days_lookup)
    quarterly = df1.groupby(['year', 'quarter'], as_index=False).apply(valid_quarter)
    return df.merge(quarterly, on=['year', 'quarter'], how='left')


def clean_colnames(df_daily):
    cols = ['_'.join(col).strip() for col in df_daily.columns.values]
    cols = [s.replace('pm2.5_', '') if '_mean' not in s else s for s in cols]
    cols = [s.replace('_mean', '') for s in cols]
    cols = [s.replace('_count','_hourcount') for s in cols]
    cols = [s+'_daily' if 'pm2.5' in s else s for s in cols]
    df_daily.columns = cols
    df_daily.insert(0, 'quarter', df_daily.pop('quarter'))
    df_daily.insert(0, 'year', df_daily.pop('year'))
    df_daily = df_daily.astype({'quarter': int, 'year': int}).reset_index()
    return df_daily


def daily_data(df: pd.DataFrame):
    """Return Daily aggregated data (means) and validity indicators for PM2.5 columns.

    For any column that has "pm2.5" in it's name, calculate the daily mean and
    count of observations that are non-missing. Create an indicator for >=
    than 75% non-missing hours (18 hours), is in NAAQS design value
     determination.
    """
    agg_dict = {col: ['mean', 'count', valid_daily] for col in df.columns if 'pm2.5' in col}
    agg_dict.update({'quarter': 'mean', 'year': 'mean'})
    df_daily = df.groupby('date_local').agg(agg_dict)
    df_daily = clean_colnames(df_daily)
    # Add indicators if quarter is valid
    df_daily = add_quarterly_valid_indicators(df_daily)
    return df_daily


def quarter_list(df: pd.DataFrame):
    df1 = df.copy(deep=True)
    dates = df1.date_local.str.split('-', expand=True)
    df1['month'], df1['day'] = dates[1], dates[2]
    # Take unique values of year-quarter and sort
    quarters = sorted(df1.year_quarter.unique())
    # Iterate down the list, starting with the 12th quarter, giving lists of 12 quarters
    lists = []
    for i in range(len(quarters)-12):
        lists.append(quarters[i:(i+12)])
    return lists


def valid_annual(x: pd.Series):
    """NAAQS design value annual average validity criterion."""
    return x.count() >= 0.75*24


def dv_annual(x: pd.Series):  # groupby.agg
    return x.mean()


def percentile98_lookup(N: int):
    """Return n, for the n'th maximum number to pick to represent the 98th percentile.

    For consisitency in calculating the 98th percentile, the EPA uses a lookup
    table to pick the n'th largest observation from the list. This depends on the
    size of the valid sample: Annual number of credible daily samples N.
    Given N, return n so we can pick the n'th max value from the daily samples.
    """
    p98 = lambda x: int(np.ceil(x/50))
    if 0 < N <= 366:
        return p98(N) - 1  # minus 1 because python is indexed from 0
    else:
        print(f'Invalid input into percentile_lookup: {N}, must be integer between 1 and 366')
        raise


def dv_hour(x: pd.Series):
    nth_max_index = percentile98_lookup(x.count())
    return x.sort_values(ascending=False).iloc[nth_max_index]


def invalid_dv(df_daily, pm_type):
    """Return true if all quarters are valid for this PM source, else False.

    The input should be a filtered df_daily, restricted to three years, since
    the completeness criteria need to be evaluated over the 3-year range of the
    design value.
    """
    return False in df_daily[f"{pm_type}_valid_quarter"].unique()


def calculate_design_values(df_daily: pd.DataFrame, quarters: list, pm_type: str):
    """Return dataframe of design values for each valid quarter ending a 12-quarter period.

    pm_type: string of the PM2.5 source to calculate the design values for.
        currently from list of 'epa' and 'pa'
    """
    # Check if DVs are valid based on all-quarters-valid criteria
    invalid = invalid_dv(df_daily, pm_type)
    if invalid:
        return pd.DataFrame({'annual': np.nan, 'hour': np.nan,
                             'pm_type': pm_type, 'year_quarter': quarters[-1]},
                            index=[0])
    # Filter out non-valid days
    df = df_daily.query(f"`{pm_type}_valid_daily`")
    # Split 12 quarters into 4-quarter years
    years = [quarters[0:4], quarters[4:8], quarters[8:12]]  # list of list of four year-quarters
    dva, dvh = [], []
    for year in years:  # list of four year-quarters
        # filter to these years
        df_temp = df[df.year_quarter.isin(year)]
        # Get design values for PM2.5 column
        agg_dict = {f"pm2.5_{pm_type}_daily": [dv_annual, dv_hour]}
        df_dv = df_temp.agg(agg_dict)
        dva.append(df_dv.T['dv_annual'].iloc[0]); dvh.append(df_dv.T['dv_hour'].iloc[0])
    # Calculate 3-year averages
    df = pd.DataFrame({'annual': np.mean(dva), 'hour': np.mean(dvh),
                       'pm_type': pm_type, 'year_quarter': quarters[-1]},
                      index=[0])
    return df


def annual_data(df_daily: pd.DataFrame, pm_type: str):
    """Return Annually aggregated data (means) and validity indicators for PM2.5 columns.

    For any column that has "pm2.5" in it's name, calculate the annual mean and
    count of observations that are non-missing. Create an indicator for >=
    than 75% valid days (18 hours), is in NAAQS design value
     determination.
    pm_column: column-name string of the PM2.5 column to calculate the design values for.
    """
    df = df_daily.copy(deep=True)
    df['year_quarter'] = df.year.astype(str) + '-' + df.quarter.astype(str)
    # Create lists of quarters in 3-year chunks
    three_year_lists = quarter_list(df)
    df_list = []
    for three_years in three_year_lists:
        # Filter to the quarters in the list
        df_temp = df[df.year_quarter.isin(three_years)]
        # DVs for the 3-year period
        df_dv = calculate_design_values(df_temp, three_years, pm_type)
        df_list.append(df_dv)
    return pd.concat(df_list, ignore_index=True)


def create_site_dvs(site_dict):
    # Load combined site data
    df = load_combined(site_dict)
    # Create qualifier / exceptional event indicator
    df = add_exceptional_indicator(df)
    # Create Summary Statistics

    # Drop Exceptional Hours
    df = df.query("drop_qualifier == False")
    # Make new combined EPA-PA column with IDW avereage PA data
    df = fill_in_missing_with_idw(df)
    # Make new combined EPA-PA column with OLS prediction from IDW PA data
    df = fill_in_missing_with_OLS(df, site_dict)
    # Make Daily dataset (with indicators for valid > 75% complete)
    df_daily = daily_data(df)
    # Calculate DVs for all quarters
    df_list = []
    for pm_type in ['epa', 'pa', 'epa.idw.pa', 'epa.olsnc.pa', 'epa.olsyc.pa', 'epa.olsyc.pa.lower', 'epa.olsyc.pa.upper']:
        df_list.append(annual_data(df_daily, pm_type))
    df_dv = pd.concat(df_list, ignore_index=True)
    df_dv['county'] = site_dict['county']; df_dv['site'] = site_dict['site']
    return df_dv


def generate_differences(df, left, right_list):
    """Return difference: subtract left from right. Positive => right is larger"""
    dfl = df[df.pm_type == left].drop(columns='pm_type')
    for right in right_list:
        dfr = df[df.pm_type == right].drop(columns='pm_type')
        dfl = dfl.merge(dfr,
                        how='inner',
                        on=['year_quarter', 'county', 'site'],
                        suffixes=(f'_{left}', f'_{right}'))  # suffixes only matters the first time
        dfl = dfl.rename(columns={'annual': f'annual_{right}', 'hour': f'hour_{right}'})  # this only renames after the first time
        dfl[f'annual_dv_diff_{right}'] = dfl[f'annual_{right}'] - dfl[f'annual_{left}']
        dfl[f'hour_dv_diff_{right}'] = dfl[f'hour_{right}'] - dfl[f'hour_{left}']
    dfl.insert(0, 'year_quarter', dfl.pop('year_quarter'))
    dfl.insert(0, 'site', dfl.pop('site'))
    dfl.insert(0, 'county', dfl.pop('county'))
    return dfl


def create_sample_dvs(left='epa', right_list=None):
    if right_list is None:
        right_list = ['epa.idw.pa', 'epa.olsnc.pa', 'epa.olsyc.pa', 'epa.olsyc.pa.upper', 'epa.olsyc.pa.lower']  #
    # Load the county-site pairs
    aqs_tbl = load_15_sites()
    diffs_list, dv_list = [], []
    # For each EPA site-county in list
    for county, site in aqs_tbl:  # cs_list
        site_dict = {'county': county, 'site': site}
        df = create_site_dvs(site_dict)
        diffs_list.append(generate_differences(df, left=left, right_list=right_list))
        dv_list.append(df)
    df_dv = pd.concat(dv_list, ignore_index=True)
    df_dv.to_csv(PATHS.data.temp / 'design_value_est.csv', index=False)
    df_save = pd.concat(diffs_list, ignore_index=True)
    df_save['invalid quarter DV due to too many missing days'] = df_save.isnull().any(axis=1)
    df_save.to_csv(PATHS.data.temp / 'design_value_differences.csv', index=False)
    agg_dict = {f'annual_dv_diff_{right}': ['mean', 'std', 'max', 'min'] for right in right_list}
    agg_dict.update({f'hour_dv_diff_{right}': ['mean', 'std', 'max', 'min'] for right in right_list})
    agg_dict.update({'invalid quarter DV due to too many missing days': ['mean', 'size']})
    df_stats = df_save.groupby(['county', 'site']).agg(agg_dict)
    df_stats.reset_index().to_csv(PATHS.data.temp / 'design_value_site-stats.csv', index=False)
    print()


def generate_predictions(df_):
    pass


################################################################################
#                       Presentation Plots
################################################################################
def add_latlon_points(df, crs, lat="Latitude", lon="Longitude"):
    points = [Point(lon, lat) for lon, lat in zip(df[lon], df[lat])]
    return gpd.GeoDataFrame(df, geometry=points, crs=crs)


def load_ca_pa_locations():
    # Load county shapefile to get CRS for purpleair locations
    p_shp = PATHS.data.gis / 'cb_2018_us_county_500k' / 'cb_2018_us_county_500k.shp'
    gdf = gpd.read_file(p_shp)
    p_pa = PATHS.data.temp / 'sensors_filtered.csv'
    cols = ['sensor_index', 'date_created', 'lat', 'lon', 'STUSPS', 'geometry']
    df = pd.read_csv(p_pa, usecols=cols)
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs=gdf.crs)
    gdf = gdf.rename(columns={'lat': 'latitude', 'lon': 'longitude', 'STUSPS': 'state'})
    gdf = gdf.query("state in ['CA']")
    return gdf


def load_ca_pa_insample(min_pa_sensors=5, dist_threshold=5):
    df = pd.read_csv(PATHS.data.tables / 'epa_pa_lookups' / f'aqs_monitors_to_pa_sensors.csv', dtype=DTYPES)
    df = df.sort_values(['county', 'site', 'dist_mile'])

    df['in_sample'] = "Other PA Sensors"

    def set_sample(df_):
        df_ = df_.reset_index(drop=True)
        if len(df_.query(f'dist_mile < {dist_threshold}')) > min_pa_sensors:
            df_['in_sample'].iloc[df_['dist_mile'] < dist_threshold] = "In Radius"
        else:
            df_.iloc[:min_pa_sensors]['in_sample'] = "In Radius"
        return df_

    df = df.groupby(['county', 'site']).apply(set_sample).reset_index(drop=True)
    return df


def plot_us_epa():
    """Plot all US EPA NAAQS sensors, mark my sample"""
    # Plot US shape
    p1 = PATHS.data.gis / 'cb_2018_us_state_5m' / 'cb_2018_us_state_5m.shp'
    gdf = gpd.read_file(p1)
    states_to_drop = ['02', '15']  # remove alaska and hawaii
    mask = "STATEFP < '60'"  # remove all non-states
    gdf = gdf[~gdf.STATEFP.isin(states_to_drop)].query(mask)
    fig = plt.figure()
    ax = gdf.plot(color='grey', figsize=(15, 8), antialiased=False)

    # Plot all EPA NAAQS monitors in black
    p2 = PATHS.data.epa_monitors / 'aqs_monitors.csv'
    df1 = pd.read_csv(p2, dtype=DTYPES)
    df1 = df1.query("`NAAQS Primary Monitor` == 'Y' and `Parameter Code` == 88101")
    df1 = df1.query("`Last Sample Date` > '2017-01-01' and `First Year of Data` < 2018")
    df1 = df1.drop_duplicates(['State Code', 'County Code', 'Site Number'])
    # 853 unique monitoring sites after this
    gdf_epa_primary = add_latlon_points(df1, gdf.crs)
    gdf_epa_primary.plot(ax=ax, color='black', markersize=11)

    # Plot selected EPA NAAQS monitors in red
    p3 = PATHS.data.epa_monitors / 'aqs_monitors_88101_hourly-ca-monitors.csv'
    df3 = pd.read_csv(p3, dtype=DTYPES)
    df3 = (df3
           .assign(state="06", in_sample=1)
           .rename(columns={'site_number': 'Site Number',
                            'county_code': 'County Code',
                            'state': "State Code"}))
    gdf_epa_sample = (gdf_epa_primary
                      .merge(df3,
                             how='left',
                             on=['State Code', 'County Code', 'Site Number']))
    gdf_epa_sample.query("in_sample == 1").plot(ax=ax, color='red', markersize=12)

    plt.xlim([-124.8, -66.9])
    plt.ylim([24.5, 49.4])
    plt.tight_layout()
    p_fig = PATHS.output / 'figures' / 'epa' / f'all_us_and_15_epa_monitors.png'
    plt.savefig(p_fig, dpi=200)
    plt.close(fig)


def plot_ca_epa():
    """Plot all ca EPA NAAQS sensors, mark my sample"""
    # Plot US shape
    p1 = PATHS.data.gis / 'cb_2018_us_state_5m' / 'cb_2018_us_state_5m.shp'
    gdf = gpd.read_file(p1)
    gdf = gdf.query("STATEFP == '06'")  # keep only CA
    ax = gdf.plot(color='grey', figsize=(8, 8), edgecolor="face", linewidth=0.4)

    # Plot all EPA NAAQS monitors in black
    p2 = PATHS.data.epa_monitors / 'aqs_monitors.csv'
    df1 = pd.read_csv(p2, dtype=DTYPES)
    df1 = df1.query("`NAAQS Primary Monitor` == 'Y' and `Parameter Code` == 88101")
    df1 = df1.query("`Last Sample Date` > '2017-01-01' and `First Year of Data` < 2018")
    df1 = df1.drop_duplicates(['State Code', 'County Code', 'Site Number'])
    df1 = df1.query("`State Code` == '06'")
    # 853 unique monitoring sites after this
    gdf_epa_primary = add_latlon_points(df1, gdf.crs)
    gdf_epa_primary.plot(ax=ax, color='black', markersize=12)

    # Plot selected EPA NAAQS monitors in red
    p3 = PATHS.data.epa_monitors / 'aqs_monitors_88101_hourly-ca-monitors.csv'
    df3 = pd.read_csv(p3, dtype=DTYPES)
    df3 = (df3
           .assign(state="06", in_sample="In Sample")
           .rename(columns={'site_number': 'Site Number',
                            'county_code': 'County Code',
                            'state': "State Code"}))
    gdf_epa_sample = (gdf_epa_primary
                      .merge(df3,
                             how='left',
                             on=['State Code', 'County Code', 'Site Number']))
    gdf_epa_sample["in_sample"].iloc[gdf_epa_sample["in_sample"] != "In Sample"] = "Other EPA Monitors"
    colors = {"In Sample": 'red', "Other EPA Monitors": 'black'}
    # gdf_epa_sample.plot(ax=ax, label="In Sample", color=colors[key], markersize=16, legend=True)
    for key, group in gdf_epa_sample.groupby("in_sample"):
        group.plot(ax=ax, label=key, color=colors[key], legend=True)
    [xmin, ymin, xmax, ymax] = gdf.bounds.values[0]
    buffer = 0.1
    plt.xlim([xmin - buffer, xmax + buffer])
    plt.ylim([ymin - buffer, ymax + buffer])
    plt.tight_layout()
    plt.legend(fontsize=17, frameon=True, facecolor='white', loc='lower left')
    p_fig = PATHS.output / 'figures' / 'epa' / f'all_ca_and_15_epa_monitors.png'
    plt.savefig(p_fig, dpi=200)


def plot_california_pa(min_pa_sensors=5, dist_threshold=5):
    """Save plot of all CA PA """
    # Load cali shape
    p1 = PATHS.data.gis / 'cb_2018_us_state_5m' / 'cb_2018_us_state_5m.shp'
    gdf = gpd.read_file(p1)
    gdf = gdf.query("STATEFP == '06'")  # keep only CA
    ax = gdf.plot(color='grey', figsize=(8, 8), edgecolor="face", linewidth=0.4)

    # Load all PA and filter to CA
    gdf_pa = load_ca_pa_locations()
    # Load PA in ranges
    df_sample = load_ca_pa_insample(min_pa_sensors=5, dist_threshold=5)
    gdf_pa = gdf_pa.merge(df_sample, on=['sensor_index'], how='left')

    gdf_pa["in_sample"].iloc[gdf_pa["in_sample"] != "In Radius"] = "Other PA Monitors"
    colors = {"In Radius": 'pink', "Other PA Monitors": 'blue'}
    zorders = {"In Radius": 10, "Other PA Monitors": 5}
    # gdf_epa_sample.plot(ax=ax, label="In Sample", color=colors[key], markersize=16, legend=True)
    for key, group in gdf_pa.sort_values('in_sample', ascending=False).groupby("in_sample"):
        print(key, colors[key])
        group.plot(ax=ax, label=key, color=colors[key], legend=True, zorder=zorders[key])
    [xmin, ymin, xmax, ymax] = gdf.bounds.values[0]
    buffer = 0.1
    plt.xlim([xmin - buffer, xmax + buffer])
    plt.ylim([ymin - buffer, ymax + buffer])
    plt.tight_layout()
    plt.legend(fontsize=17, frameon=True, facecolor='white', loc='lower left')
    p_fig = PATHS.output / 'figures' / 'pa' / f'all_ca_and_15_pa_monitors.png'
    plt.savefig(p_fig, dpi=200)



def generate_presentation_plots():
    # plot_us_epa()
    # plot_ca_epa()
    plot_california_pa()


################################################################################
#                       LaTeX Helper functions
################################################################################
def generate_latex_appendix_code(width="0.8"):
    dir1 = PATHS.output / 'figures' / 'concentric_ranges'
    dir2 = PATHS.output / 'figures' / 'epa_vs_pa'
    list1 = list(dir1.glob(f'*_epa-pa-concentric-ranges.png'))  # county-{c}_site-{s}
    list2 = list(dir2.glob(f'*_pa-daily-covereage.png'))  # site-{c}-{s}
    list3 = list(dir2.glob(f'*_epa-pa-hourly-plot.png'))  # site-{c}-{s}
    list4 = list(dir2.glob(f'*_epa-pa-missing-density.png'))  # site-{c}-{s}
    listlist = [list1, list2, list3, list4]
    prefix = 'appendix/site_plots/'
    s = ""
    section_names = ['Concentric Radii Maps',
                     'PurpleAir Hourly Observation Coverage',
                     'PurpleAir EPA Non-missing Comparison',
                     'Kernal Density Comparison']
    functionlist = [concentric_str, coverage_str, pa_epa_comparison_str, missing_density_str]
    for section, list_, func in zip(section_names, listlist, functionlist):
        s += "\n\n"
        s += section_str(section)
        for file in list_:
            name = file.name
            f = prefix + name
            county, site = get_c_s(name)
            if f"{county}-{site}" == "037-4004":  # skip this site, used as main example
                continue
            s += func(f, county, site, width=width)
            s += "\n\n"

    print(s)


def get_c_s(name):
    if "concentric" in name:
        county = name.split('county-')[1].split('_site')[0]
        site = name.split('site-')[1].split('_epa')[0]
    else:
        county, site = name.split('site-')[1].split('_')[0].split('-')
    return county, site


def section_str(section):
    return f"""
%=========================================
%  {section}
%=========================================
"""


def concentric_str(filepath, county, site, width='0.4'):
    return f"""
\\begin{{figure}}
\\centering
\\includegraphics[width={width}\\textwidth]{{{filepath}}}
\\caption{{Map of EPA NAAQS-primary monitoring station (red) surrounded by PurpleAir monitors within 5-mile (pink), 10-mile (yellow), and 25-mile (green) radii.This preliminary analysis uses the PurpleAir sensors within 5 miles (pink markers). This monitor is at site {site} in county {county} (FIPS code).}}
\\label{{fig:concentric_purpleair_{county}-{site}}}
\\end{{figure}}
"""


def coverage_str(filepath, county, site, width='0.4'):
    return f"""
\\begin{{figure}}
\\centering
\\includegraphics[width={width}\\textwidth]{{{filepath}}}
\\caption{{Scatter plot indicating the number of hours in each day that this NAAQS monitor has PurpleAir coverage. An hour has PurpleAir coverage if there are any PurpleAir sensor readings within the 5-mile radius of the monitor site for that hour. The weighted average is calculated for that hour using all the available PurpleAir readings within 5 miles. This monitor is at site {site} in county {county} (FIPS code).}}
\\label{{fig:hourly_coverage_{county}-{site}}}
\\end{{figure}}
"""


def pa_epa_comparison_str(filepath, county, site, width='0.4'):
    return f"""
\\begin{{figure}}
\\centering
\\includegraphics[width={width}\\textwidth]{{{filepath}}}
\\caption{{Scatter plot comparing reported hourly PM2.5 measurements: the x-axis represents the IDW-weighted average of PurpleAir measurements, the y-axis represents reported NAAQS-primary monitor measurements. The red line is a 45$^\circ$ line, representing perfect correlation between the PurpleAir average and the NAAQS-primary monitor. This monitor is at site {site} in county {county} (FIPS code).}}
\\label{{fig:pa-epa-compare_{county}-{site}}}
\\end{{figure}}
"""


def missing_density_str(filepath, county, site, width='0.4'):
    return f"""
\\begin{{figure}}
\\centering
\\includegraphics[width={width}\\textwidth]{{{filepath}}}
\\caption{{Comparison of PM2.5 concentration densities for two sets of hours: reported (blue) and missing (red) hourly observations of the NAAQS monitor. Both densities use the hourly PurpleAir PM2.5 concentration estimates for this site, calculated using the IDW average of PurpleAir sensors within 5 miles of the NAAQS monitor location. This monitor is at site {site} in county {county} (FIPS code).}}
\\label{{fig:missing-density_{county}-{site}}}
\\end{{figure}}
"""



"""NOTES:
Steps for PA correction to match EPA monitors from:
https://cfpub.epa.gov/si/si_public_file_download.cfm?p_download_id=540979&Lab=CEMM

Updated correction equation from EPA presentation. See docs/purpleair/purpleair_specs.md 
"""