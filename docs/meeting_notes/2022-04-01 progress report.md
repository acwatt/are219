# 2022-04-01 Progress on Second Year Paper
Aaron Watt

Using PurpleAir to Replace Missing Pollution Data

- Focusing mostly on faculty feedback from presentation



Paper by Sunday night


* Ed paper: What’s missing in environmental (self-)monitoring: Evidence from strategic shutdowns of pollution monitors
* Update introduction: broad motivation, and here's an application
    policy design depends on unbiased data. The econ lit has identified.... right now we rely on this sparse network, but we have access to a dense network of consumer sensors.
 - a variety of applications is... as has been explored earlier in the lit., we can predict the pollution during missing times
 - compared to the satellite data
 - inclusion of wildfire days
 


One possible application the this new network of PM monitors is to examine how vulnerable the current NAAQS are to manipulation. There is a line of research studying various pathways of manipulation of these standards including strategic placement of the monitor (cite), strategic communication to reduce pollution on monitoring days (cite), and strategic omission of data (Mu et al. 2021). This paper contributes to this last line of research, where Mu et al. (2021) examine plausibly strategic monitor shutdowns. They examine how full-day omissions in the regulatory monitor data are related to the local regulator's belief that high pollution is coming, proxied by local pollution alerts. This paper extends Mu et al. (2021) in two main ways: enabling the analysis of hour-level omissions in addition to day-level omissions; and examining the omission of observations that might occur after absent the local regulator's prior belief that high pollution was coming in the near future.

Extensions from Mu et al 2021:
- Mu et al look at pollution alerts which limits the study to missing day-level observations. Because I am examining hourly measurements, I can additionally study how the omission of hourly measurements can effect compliance with the standards. As Mu et al. mention, upto 25\% of daily measurements can be omitted while still complying with the federal completeness standard. Of the at least 75\% of days that must be reported, the completeness goals also allow up to 6 hours to be omitted for each reported day. This represents another possible 18.75 percentage points of hourly observations that could be omitted from the reported days while maintaining completeness, on top of up to 25\% missing full days.
- Mu et al use pollution alerts to proxy for local regulator's prediction of high pollution, allowing them to test if data are more likely to be missing when a locality has signaled their belief of higher future pollution. This examines the likelihood of missing data that coincide with predictions of high pollution, regardless if the realization of pollution measure
Findment at the location of the regulatory monitor is high or not following the pollution alert. However, there is also the possibility of data omissions resulting from high realized pollution but where no pollution alert was given (either because the high pollution was not predicted or because the prediction was not high enough to warrent a pollution alert). The concurrent PurpleAir data from sensors near the regulator monitor allow me to explore data omission occuring in all cases of realized high pollution. So an additional contribution of this application is the ability to examine missing data, possibily omitted *after* data was recorded, but in events when the high pollution was not predicted.

This paper also builds off recent literature ... Fowlie et al. ?



## 1. Develop the story of incentives more in the introduction
> Jim:  we would like to know more if possible about who has the discretion to decide what data to omit, and what their incentives are... pertains both to explaining the importance of attainment status and who the key stakeholders are to the broader audience, and offering additional insight on the details of who the “data managers” are, who hires them, and whether they are plausibly subject to pressure.

- waiting on a call-back from EPA folks to answer some questions and possibly schedule a short interview/discussion.
- will add more details to introduction


* Email Ed!



## 2. How much room is left in raw data for manipulation?
> Another exercise would be to ask how much room is left for additional manipulation. That is, suppose a data controller cared about boosting numbers and wanted to drop as many data points as would be allowed. Given the data that are being reported and the slack in the number dropped, how much of a difference would additional manipulation make? This is sort of a scale exercise for asking how useful manipulation might be.

**Reporting Standard**: 75% of days in each year, 75% (18) of hours in each day

Easy, ball-park way to implement in raw data: 
- drop all days down to the lowest 18 hours (75%)
- order remaining days from highest to lowest PM
- drop the highest days until I reach the 75% minimum reporting requirement

Hard to know if this is the absolute minimum attainable value from dropping observations but seems like it would be very close and probably similar to a heuristic used by someone on the ground.


* Ask Ed.
- where does this 75% come from, why not all data just flagged
- trade off between min reporting and NAAQS threshold

- think about the strategy







## 3. Develop motivation: how manipulatable is this measure?
> Ethan: The possibility of flipping attainment status is one way to turn this into an economics/policy narrative, but you might also consider something more broad, like stating that “effective regulation requires reliable measurement,” and then asking if the measure here is manipulable. Obviously we know that there are other types of manipulation (from prior literature), so your contribution is to look for the possibility of manipulation in this particular mechanism.

- I like this take. Switching "flipping attainment status" language to "how manipulable / reliable is this measure given the amount of legal / allowed omission of data?"






## 4. Kernel regression?
>Ethan: Isn't a kernel regression the right approach here?  Asymptotic performance of current approach (inverse distance) may not work?

- Have discussed a little bit and have more office hours scheduled
- The issue is that PurpleAir sensors are coming in and out so I don't have a balanced panel of PurleAir sensors for each EPA monitor






## 5. Regression to the mean in prediction regression
> Ethan: First table seems to involve regression to the mean (Purple Air a rhs variable, with measurement error).

- revisiting with Ethan, not sure what is to be done about this.



## 6. Multiple hypothesis testing 
> Ethan: Multiple testing (however many sites...)?  If drawing inference that a *particular* site is engaged in manipulation, current version of inference seems problematic.

- Unclear to me what the asyptotic distribution of the design values are (especially the 24-hour DV).
- Ethan and Max both directed me to talk to Michael -- seeing him on Monday.

Benjamini 2006!





## 7. Confidence intervals for non-compliant site highly asymmetric---not clear why?

- Confidence intervalus for Daily DVs are (nearly) symmetric and 24-hour DVs are highly asymmetric.
- This is expected for symmetric prediction intervals used to fill in gaps in real data.
- I added a discussion of this in the appendix and briefly reference it in the result section.





## 8. Include Wildfires
- compare with and without wildfires on reported data


Ask Ed.









## other topics:
- damage differentiated (paper with Nic Muller)
    - NOx Budget program (permits per ton)
- EPA on PA regression: include a threshold for higher PM
- bootstrapping: pick representative days (like from all weekdays in May)
    - talk to someone who knows about bootstrapping or other ways to construct confidence intervals
- Reading group for prediction exercises and inference



















