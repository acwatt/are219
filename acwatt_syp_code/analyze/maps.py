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

save_dir = Path('output/summary_stats/maps')
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
states_shp = Path('data/cb_2018_us_state_5m/cb_2018_us_state_5m.shp')
all_states = gpd.read_file(states_shp)

lower48 = (all_states
    .loc[all_states.STATEFP.astype(int) < 60]
    .loc[~all_states.NAME.isin(['Alaska', 'Hawaii'])])
california = all_states.loc[all_states.NAME.isin(['California'])]
sensor_points = [Point(xy) for xy in zip(sensor_df['lon'], sensor_df['lat'])]
sensors = gpd.GeoDataFrame(sensor_df, crs=all_states.crs, geometry=sensor_points)
sensors_lower48 = sjoin(sensors, lower48, how='inner')
sensors_california = sjoin(sensors, california, how='inner')

polygon_kwgs = {'facecolor': (100/255, 100/255, 100/255, 1),
                'edgecolor': 'white',
                'lw': 0.2}
marker_kwgs = {'facecolor': (0, 204/255, 204/255, 0.2),
               'markersize': 20,
               'marker': 'o'}

plt.style.use('ggplot')
fix, ax = plt.subplots(figsize=(7.5, 4))
world.plot(ax=ax, **polygon_kwgs)
sensors.plot(ax=ax, **marker_kwgs)
plt.title("Valid Purple Air Monitor Locations, Global")
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.tight_layout()
plt.savefig(save_dir / 'purple_air_sensor_map_global.png')


fix, ax = plt.subplots(figsize=(7, 4))
lower48.plot(ax=ax, **polygon_kwgs)
sensors_lower48.plot(ax=ax, **marker_kwgs)
plt.title("Valid Purple Air Monitor Locations, Contiguous United States")
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.tight_layout()
plt.savefig(save_dir / 'purple_air_sensor_map_us.png')

fix, ax = plt.subplots(figsize=(8, 8))
california.plot(ax=ax, **polygon_kwgs)
sensors_california.plot(ax=ax, **marker_kwgs)
plt.title("Valid Purple Air Monitor Locations, California")
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.tight_layout()
plt.savefig(save_dir / 'purple_air_sensor_map_california.png')


