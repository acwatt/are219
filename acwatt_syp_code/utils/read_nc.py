#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
from datetime import datetime, timedelta
# Third-party Imports
import netCDF4 as nc
from cftime import num2date, date2num
import cfplot as cfp
# Local Imports
#from ..utils.config import PATHS, PA, AWS, YEARS
YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021]


def download_uv_files(year):
    # dir = str(PATHS.data.gis_windspeed)
    dir = '/media/a/E/Programming/github/are219/data/gis/windspeed'
    f = nc.MFDataset(f"{dir}/*wnd.10m.{year}.nc")


import cf
import cfplot as cfp
f=cf.read('cfplot_data/tas_A1.nc')[0]
cfp.con(f.subspace(time=15), blockfill=True, lines=False)



year = 2019
component = 'u'
ufile = f'https://downloads.psl.noaa.gov/Datasets/NARR/monolevel/{component}wnd.10m.{year}.nc'
ufile = '/media/a/E/Programming/github/are219/data/gis/windspeed/uwnd.10m.2019.nc'
vfile = '/media/a/E/Programming/github/are219/data/gis/windspeed/vwnd.10m.2019.nc'
dsu = nc.Dataset(ufile)
dsv = nc.Dataset(vfile)
# Get time, lat, lon, uwnd,

# Run in mutliprocesses (each file will be in memory, 600MB, so start with 10)
# Could move to lambdas, but don't want to overwhelm their server, should limit
# to 10 simultaneous downloads anyway

# For each year
for year in YEARS:
    # Download year u and v files

    # for each EPA sensor in sensor list

        # Get sensor lat, lon

        # Get lat lon in grid that is closest to sensor (closest lat, closest lon)

        # Get u and v wind components for all times in year

        # Convert times to datatimes
        times = num2date(ds['time'], units=ds['time'].units)

        # Add u, v, sensorID, datetime to dataframe

        # Save sensor dataframe _ year to csv