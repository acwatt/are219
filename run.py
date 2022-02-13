#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import logging

import pandas as pd
# Third-party Imports
# Local Imports
import acwatt_syp_code.analyze.maps as am
from acwatt_syp_code.build import (purpleair_download,
                                   epa_download)
from acwatt_syp_code.utils.parse_epa import save_pm25_locations
from acwatt_syp_code.utils.config import PATHS
from acwatt_syp_code.build.aws import lambda_services

logger = logging.getLogger(__name__)



if __name__ == "__main__":
    logger.info('START')
    small_sample = True
    epa_monitorlist_path = save_pm25_locations(small_sample)
    epa_download.test()
    # purpleair_download.dl_us_sensors()
    # purpleair_download.test_lambda()
    # lambda_services.save_pa_data_to_s3()
    logger.info('DONE')
