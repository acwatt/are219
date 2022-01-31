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

# For Summer exporatory