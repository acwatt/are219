# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Modified by Aaron Watt, Jan 2022

"""
PURPOSE:
Writes IP address used during lambda function execution to S3 bucket CSV.
"""

import logging
import pandas as pd
import datetime as dt

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define a list of Python lambda functions that are called by this AWS Lambda function.


def get_all_week_dates(date_beg, date_end):
    # Get
    date_start = dt.datetime.strptime(date_beg, '%Y-%m-%d')
    date_end = dt.datetime.strptime(date_end, '%Y-%m-%d')
    date_list = pd.date_range(date_start, dt.datetime.today(), freq='w')
    pass


def download_sensor_week(id_, week_beg, week_end):
    # construct REST call to ThingsSpeak API

    # Download JSON response

    # Convert JSON to dataframe

    pass


def write_df_to_memcsv(df):
    # Create CSV of df in memory

    pass


def upload_s3_csv(memcsv):
    # Write fileobject to S3 bucket
    pass


def download_sensor(id_, date_beg, date_end):
    # Get sensor's creation date and last modified date
    date_beg, date_end = get_begin_end_dates(id_)

    # Get beginning and end dates of all weeks between creation and last modified
    weeks_tuple_list = get_all_week_dates(date_beg, date_end)

    # For each week
    df_list = []
    for week_beg, week_end in weeks_tuple_list:
        # Download the Purple Air sensor data to dataframe
        df_list.append(download_sensor_week(id_, week_beg, week_end))

    # Write df to CSV in memory
    df = pd.concat(df_list)
    write_df_to_memcsv(df)

    # Write S3 file
    pass


def ip_test(id_):
    # Get IP address
    # Create df of IP address
    # Create memCSV of df
    # Write CSV to S3 bucket
    # Return success or error code
    pass


def lambda_ip_s3_writer(params, bucket_dir = 'sensor_csvs'):
    """
    Accepts an action and a number, performs the specified action on the number,
    and returns the result.

    :param params: dict of dict that contains the parameters sent when the function
                  is invoked.
    :param bucket_dir: str: folder to put the CSV of downloaded purple air sensor data in
    :return: The result of the specified action.
    """
    id_ = params['sensor_id']
    created_date = params['']
    filename = bucket_dir + f'/{id_}.csv'
    logger.info(f'Sensor: {id_}')

    result = ip_test(id_)
    logger.info(f'Result of uploading IP CSV: {result}')

    # result = download_sensor(id_, params['date_created'], params['date_end'])
    # result = ACTIONS[event['action']](event['number'])
    # logger.info('Calculated result of %s', result)

    response = {'result': result}
    return response






"""
NOTES
- test very simple IP address writer asap
- need to determine how to make / break calls to get different IP addresses.

"""