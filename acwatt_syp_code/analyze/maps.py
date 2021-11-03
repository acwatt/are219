#!/usr/bin/env python

"""Functions for mapping data"""

# Built-in Imports
import pandas as pd
import matplotlib.pyplot as plt
import descartes
import geopandas as gpd
from geopandas.tools import sjoin
from pathlib import Path
from shapely.geometry import Point, Polygon

# Third-party Imports
# Local Imports

plt.style.use('ggplot')


def root_path(rootname='are219'):
    """Return pathlib path to root of git project."""
    parts = Path.cwd().parts
    i = parts.index(rootname)
    return Path(*parts[:i + 1])


def sensor_df_to_geo(df, area):
    """Return geopandas dataframes: one with sensor points, one with geographic area polygons.

    sensor_df = dataframe of sensor data, inlcuding columns = lat, lon
    area = string indicating area = ['world', 'us', 'california']
    """
    if area == 'world':
        base_gdf = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    elif area in ['us', 'california']:
        path_ = root_path() / 'data' / 'cb_2018_us_state_5m' / 'cb_2018_us_state_5m.shp'
        base_gdf = gpd.read_file(path_)
        if area == 'us':
            base_gdf = (base_gdf
                .loc[base_gdf.STATEFP.astype(int) < 60]
                .loc[~base_gdf.NAME.isin(['Alaska', 'Hawaii'])])
        elif area == 'california':
            base_gdf = base_gdf.loc[base_gdf.NAME.isin(['California'])]
    else:
        print(f'area = {area}: Not a supported area parameter.')
        raise

    sensor_points = [Point(xy) for xy in zip(df['lon'], df['lat'])]
    sensors_gdf = gpd.GeoDataFrame(df, crs=base_gdf.crs, geometry=sensor_points)
    sensors_gdf = sjoin(sensors_gdf, base_gdf, how='inner')
    return sensors_gdf, base_gdf


def sensor_plot(sensor_df, area='world', rootname='are219'):
    """Save png of plot of sensors in given geographical area.

    sensor_df = dataframe of sensor data, inlcuding columns = lat, lon
    area = string indicating area = ['world', 'us', 'california']
    """
    save_dir = root_path(rootname) / 'output' / 'summary_stats' / 'maps'

    polygon_kwgs = {'facecolor': (100 / 255, 100 / 255, 100 / 255, 1),
                    'edgecolor': 'white',
                    'lw': 0.2}
    marker_kwgs = {'facecolor': (0, 204 / 255, 204 / 255, 0.2),
                   'markersize': 20,
                   'marker': 'o'}

    figsize_dict = {'world': (7.5, 4),
                    'us': (7, 4),
                    'california': (8, 8)}

    sensor_gdf, base_gdf = sensor_df_to_geo(sensor_df, area)

    fix, ax = plt.subplots(figsize=figsize_dict[area])
    base_gdf.plot(ax=ax, **polygon_kwgs)
    sensor_gdf.plot(ax=ax, **marker_kwgs)
    location = area.upper()*(area == 'us') + area.title()*(area != 'us')
    plt.title(f"Valid Purple Air Monitor Locations, {location}")
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.tight_layout()
    plt.savefig(save_dir / f'purple_air_sensor_map_{area}.png')


def make_all_sensor_maps(sensor_df):
    for area in ['world', 'us', 'california']:
        sensor_plot(sensor_df, area=area, rootname='are219')
