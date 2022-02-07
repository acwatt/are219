# [PRISM](https://prism.oregonstate.edu/documents/PRISM_datasets.pdf)
> PRISM datasets provide estimates of seven primary climate elements: precipitation (ppt), minimum temperature
(tmin), maximum temperature (tmax), mean dew point (tdmean), minimum vapor pressure deficit (vpdmin),
maximum vapor pressure deficit (vpdmax), and total global shortwave solar radiation on a horizontal surface
(soltotal; available only as normals at this time).

# EPA
- Need to download hourly data (and other aggregation levels) for EPA PM2.5 data from all 88101 sensors

# Windspeed
- [NOAA](https://www.ncdc.noaa.gov/cdo-web/)
- [Climate.gov monthly windspeed](https://www.climate.gov/maps-data/dataset/average-wind-speeds-map-viewer)
- [NCEP North American Regional Reanalysis (NARR) ](https://psl.noaa.gov/data/gridded/data.narr.html) as from Deryugina paper in 261
    - u/v components of wind velocity at 10m above surface ==> wind speed and direction
      - uwnd.10m.yyyy.nc and vwnd.10m.yyyy.nc 
    - every 3 hours, 10m above surface
    - approximately 32km x 32km
    - Please note: If you acquire NCEP Reanalysis data products from PSL, we ask that you acknowledge us in your use of the data. This may be done by including text such as NCEP Reanalysis data provided by the NOAA/OAR/ESRL PSL, Boulder, Colorado, USA, from their Web site at /
    - Missing data is flagged with a value of 9.96921e+36f.

## NC files
- [netCDF Conventions / data formatting](https://psl.noaa.gov/data/gridded_help/conventions/cdc_netcdf_standard.shtml)
- [What is netCDF](https://psl.noaa.gov/data/gridded/whatsnetCDF.html)
- [How to Read PSL's netCDF Files](https://psl.noaa.gov/data/gridded_help/read-our-files.html)
  > All of our data are stored in netCDF files. The times are encoded as the number of hours (or days) since 1-1-1 00:00:0.0 (or 1800-1-1 00:00:0.0) using the UDUNITS library.
- [Reading NetCDF files with python](https://towardsdatascience.com/read-netcdf-data-with-python-901f7ff61648)
