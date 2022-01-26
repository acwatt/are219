#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import logging

import pandas as pd
# Third-party Imports
# Local Imports
import acwatt_syp_code.analyze.maps as am
import acwatt_syp_code.build.purpleair_download as pad
from acwatt_syp_code.utils.config import PATHS
from acwatt_syp_code.build.aws import lambda_services

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info('START')
    pad.dl_us_sensors()
    # pad.test_lambda()
    # lambda_services.save_pa_data_to_s3()
    logger.info('DONE')
