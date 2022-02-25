


# Policy analysis
- How do predicted attainment statuses compare to psuedo attainment statuses (and real)
- How does the differenece in attainment status (or design value) change with variables? Can we explain the differences betw in vars that we expect and vars that we are concerned about (demographics)


# Final outputs
- 3-way design value table (real, pseudo, estimated without missing)
- maps of counties
  - heat map based on the size of difference btween the pseudo and estimated design values 
  - categorized map based on aggree or disagree (or 4 colors: aggree on non-attainment, aggree on attainment, pseudo=attain but est=nonattain (RED), pseudo=nonattain but est=attain)


# Big questions about analysis
- should I be examining design values from combination of PA and EPA, or just use PA to created predicted PM2.5 readings of the EPA and only look at design values based on the PA estimated PM?
- Do I need to keep the # of PA sensors constant for a given year or quarter to calculate SEs?
  - What is the uncertainty in each hour measurement? (95% min and max of device spec)
  - What is the uncertainty in the weighted average? (95% lowerbound from wavg of 95% mins)
  - What is the uncertainty in predicting the EPA's PM with weighted avg? (just regression SEs? Assuming classical measurement error of the PA sensors. Could flag all missing from PA, then use all other PA to predict missing PA for each PA and see if there is a bias in the missing. Hopefully random, but perhaps more errors occur when pollution is higher? Perhaps people worry more about pollution and move their sensors around when pollution is higher?)
  - What is the uncertainty in predicting the EPA's PM with regression of PA sensors?
- Are all the qualifiers indicators for that hour's NAAQS removal?