1. Confidence intervals for mutliple hypotheses

2. permutation p-values with non-random treatment / selection / censorship of data based on treatment

missing at random: flip a coin, missing

missing at random, but serially correlated: given an hour is missing, the next hour is more likely to be missing
serial correlation impacts calculation of SEs.
Can use permutation p-values, but need to be faithful to the orignal treatment assignment.
Need to build in serial correlation. randomly assign episodes of missing chunks.
Stage 1: estimate distribution of how long contiguous missing chunks are
Stage 2: permute, randomly assign missing, then length.
