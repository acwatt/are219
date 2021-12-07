# 2021-11-30
Deryugina: Wind speed and wind direction data for the years 1999–2013 are obtained from
the North American Regional Reanalysis (NARR)

temperature and precipitation data from Schlenker and Roberts
(2009), which produces a daily weather grid using data from PRISM and weather
stations.


# 2021-11-29
Added map of EPA 88101 EPA sensors and PA sensors.
Version 1: select EPA monitors that have PA monitors within 50 miles and use model
Version 2: use all PA monitors in ML prediction for all EPA monitors + wind speed and winddir at EPA site.

Need to filter PA based on location stars.



# 2021-11-28
Drafted the 5-min presentation. Much more material than I have time for, so I need to boil it down to just what Joe asked for and practice timing.

Sent a copy of the long version to Meredith -- maybe she'll be able to get back to me?



# 2021-11-02
Unsure if python wrapper will properly bulk download the data -- don't want to make too many repeated requests or I might get blocked by the purpleair firewall

Tried the map download tool. Worked for campus over 2 days, but did not work for all of berkeley over one year.
Try all of berkeley over two days and shift upward.
Should try to see if rest request is easy to get bulk data given list of sensors.


# 2021-11-01
Found purple air API python wrapper: https://github.com/ReagentX/purple_air_api

Next: 
- can I combine `sensor_filter`s (useful + outside)?
- can I get all channels? What to do with both channels? Check if they agree per [purple air doc](https://docs.google.com/document/d/15ijz94dXJ-YAZLi9iZ_RaBwrZ4KtYeCy08goGBwnbCU/edit)
  - PurpleAir sensors employ a dual laser counter to provide some level of data integrity. This is intended to provide a way of determining sensor health and fault detection. Some examples of what can go wrong with a laser counter are a fan failure, insects or other debris inside the device or just a layer of dust from long term exposure. 

    If both laser counters (channels) are in agreement, the data can be seen as excellent quality. If there are different readings from the two channels, there may be a fault with one or both.

    In the case of a fault, the channel may be marked as flagged or downgraded (suspect or known faulty).

- filter lat lons in california border
- download historical data for all sensors in california

EPA:
- figure out the difference between PM2.5 measures
  - FRM / FEM / non-FRM PM2.5
  - PM2.5 FRM/FEM Mass
  - PM2.5 non FRM/FEM Mass
  - PM2.5 Speciation
  - [see particulates here](https://aqs.epa.gov/aqsweb/airdata/download_files.html#Raw)
- check for python / R wrapper for [EPA sensors API](https://aqs.epa.gov/aqsweb/documents/data_api.html#variables) or look in [pre-generated files](https://aqs.epa.gov/aqsweb/airdata/download_files.html#Raw)
