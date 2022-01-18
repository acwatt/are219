#!/usr/bin/env python

"""Module Docstring"""

# Built-in Imports
import pandas as pd
# Third-party Imports
# Local Imports
import acwatt_syp_code.analyze.maps as am
import acwatt_syp_code.build.purpleair_download as pad
from acwatt_syp_code.utils.config import PATHS
from acwatt_syp_code.build.aws import lambda_services

if __name__ == "__main__":
    print('START')
    pad.dl_us_sensors()
    # lambda_services.save_pa_data_to_s3()
    print('DONE')