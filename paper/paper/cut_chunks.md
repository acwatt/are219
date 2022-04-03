# Titles
The Pollution Impacts of Low Reporting Standards


# Introduction
 
% Air quality in the United States has largely been measured by a network of air quality monitoring stations overseen by the Environmental Protection Agency (referred to as ``monitors'' for the rest of this paper).
% %
% The Environmental Protection Agency (EPA) employs these monitors to track progress and enforce air quality standards developed in the US Clean Air Act and it's Amendments (CAAA) in the 1960s and 70s.
% %
% These National Ambient Air Quality Standards (NAAQS)


%
The United States implemented a network of air quality monitors in the 1970s that report air quality to regulators.
%
These air quality monitors are managed by local and state officials who control when the monitors are on or off.
%
These local and state officials are part of the organization that would receive sanctions if air quality in their region falls below federal standards.
%
Given the potential for large fines and costly, forced technology adoption, incentives exist to behave strategically within this reporting system.
%
Additionally, federal regulations have wiggle room in what portion of air quality readings need to be valid.
%
For instance, when measuring particulate matter in the air (one of the most common types of pollution), the EPA allows up to 25\% of measurements to be missing or omitted \citep{epa_appendix_2017}.
%
There are currently no restrictions for which 75\% of readings must be reported.
 
 
 
These monitors have been a necessary component of major improvements to air quality\footnote{The estimated average emissions of six important air pollutants has decreased by more than half between 1990 and 2010 \citep{epa_our_2012}.}. 

Setting air quality standards and regulating geographical areas that fall outside those standards is an important channel through which air quality improvements are made.

Yet measuring and reporting air quality at all times of the day still remains a challenge; this challenge is reflected in the flexibility of the EPA's air quality measurement rules.


How would filling in missing air quality data at EPA monitoring stations impact the regulation of pollution in the US? 





In calculating design values based on hourly measurements, missing data can lead to measurement error in reported PM2.5. When these data are not missing at random, we no longer can assume classical measurement error and we begin to move away from the usual attenuation bias results. There has been a long history in economics literature regarding the effect of missing data values and measurement error \citep{schennach_recent_2016}. However, more recent work relates to the measurement of air quality in the US. 



Over the last decade, there has also been a growing number of consumer products that are able to measure air quality.
%
The PurpleAir company produces relatively cheap outdoor air quality monitors that can measure local PM2.5 concentrations (along with other pollutants).
%
While these consumer air quality monitors do not have as rigorous data quality checks as the more expensive EPA-grade monitors, there are a growing number of PurpleAir sensors across the US that are running around the clock.
%
Can PurpleAir sensors help fill in the gaps of the official air quality measurements reported to the EPA?
%
Specifically, is it possible to use data from PurpleAir monitors to 




Using wind speed and direction, I create weights for PurpleAir sensors near the monitoring station, with larger weights going to PurpleAir sensors that have more power to predict the PM2.5 levels at the station






# Background

States must submit and adopt implementation plans to keep their ambient air quality within the NAAQS-specified levels. These implementation plans must detail how the state is going to monitor, report, and control the emissions made within their jurisdiction. The EPA can delegate its regulatory authority to the state to ensure the plans are enacted and has authority to impose large fines\footnote{on the order of \$25,000-\$50,000 per day and possible prison time} to any owner or operator of a pollution-producing facility who is purposefully violating emissions standards. 





# Model
\section{Modeling Missingness in time}
EPA pollution monitors can be turned on and off buy the hour and day, but have a constraint on the maximum number of hours per week they can be turned off. Consider the following probit model of missing pollution data
\[
D_{h,d,y,c} = \beta_0 + \beta_1 P_{h,d,y,c} 
+ \beta_2 X_{c,y} + \beta_3\delta_h + \beta_4\delta_d +\beta_5\delta_y
\]

where in hour-day-of-the-week




40 CFR §50 App. N


