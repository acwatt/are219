# 2022-04-04 Meeting with Ed Rubin

Prep:
- Read What’s missing in environmental (self-)monitoring: Evidence from strategic shutdowns of pollution monitors
-

# Questions:
## 1. data managers
we would like to know more if possible about who has the discretion to decide what data to omit, and what their incentives are... pertains both to explaining the importance of attainment status and who the key stakeholders are to the broader audience, and offering additional insight on the details of who the “data managers” are, who hires them, and whether they are plausibly subject to pressure.


1.b Do you know if the data are automatically uploaded during measurement to AQS? Or is there a chance to not report data *after* it's been recorded by looking at the measurements and deciding to omit data points?



"we know that there's other cases of 
cobit grainger citing of monitors
- how they cite busineses (big polluters) around the monitors
- air qualtiy district people actually change where businesses cite because it would be unfair if a big polluter was right upwind, so they ask them to go east so they aren't blowing their pollution directly into their monitor.

as Exceptional events excpetions get more avialable, strategic gaming seems to be going down because



Water:
- Shaoda Wang water paper (from ARE), chinese regulation of water, upstream and downstream polluters (regulate upstream more)
- Will Weeler (epa) lead and copper rule: 98th percentile, but very loose guidelines for monitoring water. No penalty for extra sampling on cleaner days.
- 

Dave McGloughlin (environmental defense fund) super nice contact


## 2. How much room is left in raw data for manipulation?
Easy, ball-park way to implement in raw data: 
- drop all days down to the lowest 18 hours (75%)
- order remaining days from highest to lowest PM
- drop the highest days until I reach the 75% minimum reporting requirement

The brute force way would be to look at all possible combinations of hours that could be dropped and still maintain the minimum reporting threshold. That's a (24*365) choose (6*365) combinatorics problem (roughly 2*10^2137) that I would like to avoid. Does the easy way above seem reasonable to you?

* Look at the old ozone rule -- something strange like only running the monitors between 10am and 6pm.
 - good motivation for why hourly manipulation could be reasonble

* compare different frequency of dropping (hourly or daily and both)



Behavioral model of what the local regulator is doing. Rubin's is just trying to stay below the standard. Could use more principle-agent regulation models. Say a local regulator wants to "capture average pollution at my monitor", and we give her some flexibility to monitor, what would be needed 


Meredith has a friend at the EPA Dave Evans, maybe Dave would be willing to look at my paper and talk about the behavior of local regulators.
CEE


## 3. Multiple hypothesis testing: 1,359 monitors













- maybe talk to a local air quality district person
- School of information: prediction class (data science, machine learning)
- Sol Hsiang spatial
- Josh Blumenstock









