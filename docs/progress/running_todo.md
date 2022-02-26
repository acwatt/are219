# Imminent
- Create toy example
  - Pick one EPA sensor that has hourly data and plenty of PA sensors around it
  - Filter in PA sensors within 25 mi radius
  - Get beginning and end date of sensor
  - Get beginning and end dates of all PA sensors in radius
  - Generate list of quarters and which sensors to include
    - only include sensors that have no missing hours? Above 75% of hours? Could imput the missing hours with the mean, or for each hour, create prediction where weights are devided by sum of non-missing-sensors' weights... 
  - Create prediction of EPA values
    - compare predicted during non-missing to actual EPA values
    - 
- Get Purple Air Data
- Get NAAR windspeed data
- Load / filter EPA sensors
  - get list of sensor
  - be able to load each sensors data
  - apply toy example to 5 sensors



# Within 2 weeks
- Get census data for toy example
- Get/request air advisory data
- Flow diagram for AQI advisory notices. 
- Setup Census download for any county

# Analysis
- Analysis of design value difference and demographics
  - regression?
  - Diff-in-diff across attainment threshold? Places on either side of the threshold might be close in many ways, but one has avoided a non-attainment status and the fines.


# Paper
- Fix long line in Qualifier exclusions table
- Finish data cleaning steps table
- Get information on which counties are currently in attainment

# For Summer exporatory


# Code Modifications:
- IDW: change from just within radius or min number to min number within 25 mi to cover most dates
- Use all within 25 mi in predictive, maybe lasso out the non-predictive ones.
- For monitors that have few sensors, multiple didn't download originally so should either be removed from the lookup table
  or the algo should keep moving down the list until min_sensors is reached.
- Download sensors from S3 using threads to increase download.
  - Cache sensors that are used multiple times (load all lists first, check which are used multiple times.)
  - Implement max sensors per EPA monitor?
- Fix following issue:
  ```shell
   See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
    df['pm2.5_epa.olsyc.pa.upper'] = np.where(df['pm2.5_epa'].isna(), df['upper.yc'], df['pm2.5_epa'])
  /media/a/E/Programming/github/are219/acwatt_syp_code/build/calculate_pm.py:436: SettingWithCopyWarning: 
  A value is trying to be set on a copy of a slice from a DataFrame.
  Try using .loc[row_indexer,col_indexer] = value instead
  ```














