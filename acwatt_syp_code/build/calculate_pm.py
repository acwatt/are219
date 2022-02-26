#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import logging
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import os
import io
# Third-party Imports
import boto3
from botocore.exceptions import ClientError
# Local Imports
from ..utils.config import PATHS, AWS

logger = logging.getLogger(__name__)
DTYPES = {"county": str, "site": str, "Qualifier Type Code": str}


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
    logger.info(f"Loading EPA data for site {county}-{site}")
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


def concat_sensors(sensor_list: pd.DataFrame, power=1):  # IDW power
    df_list = []
    for sensor_id, dist in zip(sensor_list['sensor_index'], sensor_list['dist_mile']):
        print(f'Starting sensor {sensor_id}')
        # Downlaod the file to dataframe
        bucket_file = f'{sensor_id:07d}.csv'
        df_pa = download_file(AWS.bucket_name, bucket_file)
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


def filter_sensors(sensor_list, threshold, min_sensors=10):
    if len(sensor_list.query(f"dist_mile < {threshold}")) >= min_sensors:
        return sensor_list.sort_values('dist_mile').query(f"dist_mile < {threshold}")
    else:
        return sensor_list.sort_values('dist_mile').iloc[0:min_sensors]


def add_pa_pm(df_epa, county, site, threshold=5, power=1, min_sensors=10):
    logger.info(f"Adding PurpleAir PM data to EPA data for site {county}-{site}.")
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
            logger.info(f'Starting PA weighted average for site {county}-{site}')
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
    df_daily.columns = ['_'.join(col).strip() for col in df_daily.columns.values]
    df_daily = df_daily.rename(columns={'quarter_mean': 'quarter', 'year_mean': 'year',
                                        'pm2.5_epa_mean': 'pm2.5_epa_daily',
                                        'pm2.5_epa_count': 'epa_hourcount',
                                        'pm2.5_epa_valid_daily': 'epa_valid_daily',
                                        'pm2.5_pa_mean': 'pm2.5_pa_daily',
                                        'pm2.5_pa_count': 'pa_hourcount',
                                        'pm2.5_pa_valid_daily': 'pa_valid_daily'})
    df_daily = df_daily.astype({'quarter': int, 'year': int}).reset_index()
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
    print('Invalid?', invalid)
    if invalid:
        return pd.DataFrame({'annual': -9999, 'hour': -9999,
                             'pm_type': pm_type, 'year_quarter': quarters[-1]},
                            index=[0])
    # Filter out non-valid days
    df = df_daily.query(f"{pm_type}_valid_daily")
    # Split 12 quarters into 4-quarter years
    years = [quarters[0:4], quarters[4:8], quarters[8:12]]  # list of list of four year-quarters
    dva, dvh = [], []
    for year in years:  # list of four year-quarters
        print('year', year)
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
        print('three_years', three_years)
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
    # Make Daily dataset (with indicators for valid > 75% complete)
    df_daily = daily_data(df)
    # Calculate DVs for all quarters
    pm_type = 'epa'
    df_list = []
    for pm_type in ['epa', 'pa']:
        print('starting PM source', pm_type)
        df_list.append(annual_data(df_daily, pm_type))
    df_dv = pd.concat(df_list, ignore_index=True)
    df_dv.to_csv(PATHS.data.temp / 'design_value_est.csv', index=False)


def create_sample_dvs():
    site_dict = {'county': '037', 'site': '4004'}
    create_site_dvs(site_dict)



#
# site_dict = {'county': '037', 'site': '4004'}
# create_site_dvs(site_dict)


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