#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import logging

import pandas
# Third-party Imports
# Local Imports
import acwatt_syp_code.analyze.maps as am
from acwatt_syp_code.build import (purpleair_download,
                                   epa_download,
                                   calculate_pm)
from acwatt_syp_code.utils.parse_epa import save_pm25_locations
from acwatt_syp_code.utils.config import PATHS
from acwatt_syp_code.build.aws import lambda_services

logger = logging.getLogger(__name__)

# Set pandas settings
pandas.set_option('display.width', 320)
pandas.set_option('display.expand_frame_repr', True)
pandas.set_option('display.max_rows', 20)
pandas.set_option('display.min_rows', 50)
pandas.set_option('display.max_columns', 250)


if __name__ == "__main__":
    logger.info('START')
    small_sample = True
    # epa_monitorlist_path = save_pm25_locations(small_sample)
    # epa_download.download_15_test_sites()
    # purpleair_download.dl_us_sensors()
    # purpleair_download.test_lambda()
    # lambda_services.save_pa_data_to_s3()
    # calculate_pm.combine_15_sites(run_all=True)
    # calculate_pm.make_plots_15_sites()
    # calculate_pm.create_sample_dvs()
    calculate_pm.create_minimum_dvs()
    calculate_pm.generate_presentation_plots()
    logger.info('DONE')
