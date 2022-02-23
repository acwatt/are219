#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
import seaborn as sns
# Third-party Imports
# Local Imports

"""Purpose
EPA NAAQS design values come in two forms: a 3-year running average of daily averages
and a 3-year running average of annual 98th percentiles of daily averages. The
Law of Large Numbers would apply faily easily to the first design value, so 
as we add more iid observations to the design value calculation, we would get closer
to the population average. But it's unclear to me what happens to the 98th percentile
design value when we add more idd observations. This is my attempt to numerically
answer that question with a small example by comparing the 98th percentile of 100
iid observations with the 98th percentile of 1000 observations.
"""

percentiles, size = [], []
for n in range(200, 400):
    data_normal = norm.rvs(size=n, loc=10, scale=3)
    size.append(n)
    percentiles.append(np.percentile(data_normal, 98))
    print('*', end='')
    # plt.figure()
    # sns.kdeplot(np.array(data_normal))

plt.figure()
plt.plot(size, percentiles, '-o')
