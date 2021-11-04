#!/usr/bin/env python

"""Functions for mapping data"""

# Built-in Imports
import json
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import seaborn as sns
from pathlib import Path
from shapely.geometry import Point
# Third-party Imports
# Local Imports
from ..utils.config import PATHS

plt.style.use('ggplot')


def sensor_df_to_geo(df, area):
    """Return geopandas dataframes: one with sensor points, one with geographic area polygons.

    df = dataframe of sensor data, inlcuding columns = lat, lon
    area = string indicating area = ['world', 'us', 'california']
    """
    if area == 'world':
        base_gdf = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    elif area in ['us', 'california']:
        path_ = PATHS.data.gis / 'cb_2018_us_state_5m' / 'cb_2018_us_state_5m.shp'
        base_gdf = gpd.read_file(path_)
        if area == 'us':
            base_gdf = (base_gdf
                .loc[base_gdf.STATEFP.astype(int) < 60]
                .loc[~base_gdf.NAME.isin(['Alaska', 'Hawaii'])])
        elif area == 'california':
            base_gdf = base_gdf.loc[base_gdf.NAME.isin(['California'])]
    elif area == 'benton county':
        path_ = PATHS.data.gis / 'cb_2018_us_county_500k' / 'cb_2018_us_county_500k.shp'
        base_gdf = gpd.read_file(path_)
        base_gdf = (base_gdf
            .loc[base_gdf.STATEFP.astype(int) == 41]
            .loc[base_gdf.NAME == 'Benton'])
    else:
        print(f'area = {area}: Not a supported area parameter.')
        raise

    sensor_points = [Point(xy) for xy in zip(df['lon'], df['lat'])]
    sensors_gdf = gpd.GeoDataFrame(df, crs=base_gdf.crs, geometry=sensor_points)
    sensors_gdf = gpd.tools.sjoin(sensors_gdf, base_gdf, how='inner')
    return sensors_gdf, base_gdf


def sensor_plot(sensor_df, area='world', dpi=300):
    """Save png of plot of sensors in given geographical area.

    sensor_df = dataframe of sensor data, inlcuding columns = lat, lon
    area = string indicating area = ['world', 'us', 'california']
    """
    polygon_kwgs = {'facecolor': (100 / 255, 100 / 255, 100 / 255, 1),
                    'edgecolor': 'white',
                    'lw': 0.2}
    marker_kwgs = {'facecolor': (0, 204 / 255, 204 / 255, 0.2),
                   'markersize': 20,
                   'marker': 'o'}
    figsize_dict = {'world': (7.5, 4),
                    'us': (7, 4),
                    'california': (8, 8),
                    'benton county': (8, 8)}

    sensor_gdf, base_gdf = sensor_df_to_geo(sensor_df, area)

    fix, ax = plt.subplots(figsize=figsize_dict[area])
    base_gdf.plot(ax=ax, **polygon_kwgs)
    sensor_gdf.plot(ax=ax, **marker_kwgs)
    location = area.upper()*(area == 'us') + area.title()*(area != 'us')
    plt.title(f"Valid Purple Air Monitor Locations, {location}")
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.tight_layout()
    save_dir = PATHS.output / 'summary_stats' / 'maps'
    plt.savefig(save_dir / f'purple_air_sensor_map_{area.replace(" ","_")}.png', dpi=dpi)


def match_(shortStrList, longStr):
    try:
        return next(s for s in shortStrList if s in longStr)
    except StopIteration:
        return pd.NA


def weighted_average(df, data_col, weight_col, by_col):
    df['_data_times_weight'] = df[data_col]*df[weight_col]
    df['_weight_where_notnull'] = df[weight_col]*pd.notnull(df[data_col])
    g = df.groupby(by_col)
    result = g['_data_times_weight'].sum() / g['_weight_where_notnull'].sum()
    del df['_data_times_weight'], df['_weight_where_notnull']
    return result


def culumative_time_plot(dpi=300):
    # Purple Air Data (date created for all current california sensors)
    date_file = PATHS.data.test_data / 'date_created_california_manual_request.txt'
    dict_ = json.load(open(date_file,))
    df1 = (pd.DataFrame(dict_['data'], columns=dict_['fields'])
          .assign(date_start=lambda x: pd.to_datetime(x['date_created'], unit='s')))
    # EPA AQI data on the same period (2016-2021)
    df2 = (pd.concat([pd.read_csv(p) for p in (PATHS.data.epa / 'aqi').glob('*csv')],
                   ignore_index=True)
           .filter(['State Name', 'county Name', 'Date', 'AQI'])
           .groupby(['State Name', 'county Name', 'Date'])
           .mean()
           .reset_index())
    df2 = df2[df2['State Name'] == 'California'].drop('State Name', axis=1)
    # County populations (to create weighted state average AQI per day)
    df3 = pd.read_excel(PATHS.data.gis / 'co-est2019-annres-06.xlsx',
                        header=3, usecols=[0, 9])  # 2016 estimates
    df3['pop_weight'] = df3[2016] / df3[2016].sum()
    counties = df2['county Name'].unique()
    df3['county Name'] = df3['Unnamed: 0'].apply(lambda x: match_(counties, x))
    df2 = (df2
           .merge(df3, how='left', on='county Name')
           .drop(['Unnamed: 0'], axis=1))
    df4 = weighted_average(df2, 'AQI', 2016, 'Date').reset_index()
    df4['Date'] = pd.to_datetime(df4['Date'])
    df4['aqi_7day_ave'] = df4[0].rolling(7).mean().shift(-3)
    df4['aqi_20day_ave'] = df4[0].rolling(20).mean().shift(-10)

    plt.style.use('ggplot')
    ax1 = (df1
           .set_index('date_start')
           .sort_index()
           .assign(count=1/1000)
           .cumsum()[['count']]
           .plot(figsize=(8, 6), color='blue'))
    ax2 = ax1.twinx()
    ax2.spines['right'].set_position(('axes', 1.0))
    df4.set_index('Date')[['aqi_20day_ave']].plot(ax=ax2)
    ax1.set_xlabel('Date existing sensor turned on')
    ax1.set_ylabel('Count of sensors (1000s)')
    ax2.set_ylabel('20-day rolling average AQI in CA\n(population-weighted state average)')
    plt.title('Cumulative distribution of Purple Air sensors in California\nand State Average AQI')
    plt.tight_layout()
    save_dir = PATHS.output / 'summary_stats' / 'graphs'
    plt.savefig(save_dir / f'purple_air_sensor_cum_time_california.png', dpi=dpi)


def aqi_time_plot():
    df = pd.concat([pd.read_csv(p) for p in PATHS.data.epa.glob('*csv')],
                   ignore_index=True)
    dfs = [pd.read_csv()]


def make_all_sensor_maps(sensor_df):
    for area in ['world', 'us', 'california', 'benton county']:
        sensor_plot(sensor_df, area=area)
    culumative_time_plot()
