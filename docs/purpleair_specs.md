From
EPA, Office of Research & Development. “Air Sensors: PurpleAir, AirNow Fire and Smoke Map, and Their Use Internationally.” Accessed November 22, 2021. https://cfpub.epa.gov/si/si_public_record_Report.cfm?dirEntryId=350379&Lab=CEMM.

Johnson, K., S. Frederick, A. Holder, AND A. Clements. Air Sensors: PurpleAir, AirNow Fire and Smoke Map, and their use Internationally. U.S. State Department Embassy Fellows Program Monthly Virtual Meeting, Durham, NC, December 03, 2020.

- 2 sensors (channels)
- channels alternate 10 sec sampling intervals
- reports 2 min averages

outputs:
- particle count by size
- PM1, PM2.5, PM10 with 2 corrections available (correction factors CF)
- CF=atm (for lower concentrations, used for outdoor sensors)
- CF=1 (higher concentrations, used for indoor sensors)
- Internal temp, relative humidity, pressure
- data stored locally on microSD

Data cleaning:
- Agreement between A and B channels provides
confidence in measurements
- Points removed if 24-hr averaged A & B PM 2.5 channels differed by
  - ≥ ± 5 µg m -3 AND
  - ≥ ± 62% (95% Confidence interval on % error [2*standard deviation(% error)])
- 2% of points of full dataset excluded (what % do I exclude using these thresholds?)
- 19/53 sensors had at least 1 point removed (36%) (how many sensors do I have with at least one point removed?__)
- A & B channels averaged to increase certainty

Resulting Correction Equation (updated in 2021: https://www.epa.gov/air-sensor-toolbox/technical-approaches-sensor-data-airnow-fire-and-smoke-map)
PA_CF1 <= 343 (raw) or <= 176-185 as measured by corrected sensor
PM 2.5 corrected= 0.524*[PurpleAir CF=1; avgAB ] - 0.0852*RH + 5.72
- PM 2.5 = (µg m -3 ) 
- RH = Relative Humidity (%)
- PA cf=1; avgAB = PurpleAir higher correction factor data averaged from the A and B channels

PS_CF1 > 343 ugrams/m^3 (207 as measured by corrected sensor)
PM2.5 corrected= 0.46*[PurpleAir CF=1; avgAB ] + 3.93*10^-4*[PurpleAir CF=1; avgAB ]^2 + 2.97

Picked the threshold point to be in the middle of the very unhealthy AQI category.