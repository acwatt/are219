# 2022-01-28 Meeting with Meredith
## Data
- Purple Air
- Windspeed and direction from North American Regional Reanalysis (NARR)
    - Meredith said she would ask Ed Rubin about getting hourly data.
- Get real design values and keep in a 3-way table for comparison (real, pseudo, estimated without missing)

- Learn more about hourly EPA measurements: is it really that accurate? Do I need to collapse to the day level. Eric Zou might know more, or just look it up.


## Analysis
- Lambda function for each sensor
- how does the differernce between the psuedo design value
Conditional on the difference, how does the probability of being in a non-attaninment area change with vars we expect to effect it (geography, climate, population) vs vars we are concerned about it (race, income, other demographics)

Andrew Plantenga and ...
- modeling wildfire spread, looking at real wildfire spread, and can we explain the differences betw in vars that we expect and vars that we are concerned about (demographics)

Two lines of paper:
- design values (DV) if differences in predicted and reported DV are large and non-random .... biased measure of attainment
- advisory notices -- are the advisry notices based on EPA data. If the EPA data is not missing at random (biased downward), does this impact advisory notices in any important ways that are correlated with 

Get: 
- Flow diagram for AQI advisory notices. 
- EPA actual design values


# 2022-01-26
## Purple Air Lambda Function download partially successful, but getting data another way
- Purple air downloader using AWS lambda functions was successful, but overly parallized. Meredith got an email from Purple Air asking us to stop the downloading because it was overloading the ThingSpeak servers.
- Adrian Dybwad <adrian@purpleair.com> asking us to call him. I did and he said they can probably give us the Purple Air data we're looking for using a recently updated Google BigQuery data dump. They have up to Oct 2021. Adrian ask me to send him an email with the request.
- We're corresponded a couple times -- I've given him a CSV of the sensor IDs I want (2022-01-27). Waiting on a response.

## Continued work
I've spent too much time on trying to download the PA data. Need to work on:
- Downloading the wind/temperature data 

# 2022-01-10
- Creating algorithm map
- Setup S3 bucket
- Setup IAM user role to download and upload to S3 and create/use lambda service (to use from inside python controller script)
- Create lambda service to copy that has python code in it. Or maybe just need .py file to run in lambda?
- Test lambda service to download PA data and save to S3 bucket


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
