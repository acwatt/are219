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
import requests
import os
import threading

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define a list of Python lambda functions that are called by this AWS Lambda function.
def round_down_halfyear(dt_obj):
    # Round month down to beginning of 6-month period
    month = 1 + round(dt_obj.month/12) * 6
    return dt.date(dt_obj.year, month, 1)


def round_up_halfyear(dt_obj):
    # Add 6 months and round down
    dt_obj = dt_obj + dt.timedelta(days=366/2)
    return round_down_halfyear(dt_obj)


def add_six_months(date_str: str):
    d = dt.datetime.strptime(date_str, "%Y-%m-%d")
    d = round_up_halfyear(d)
    if d > dt.datetime.today():
        d = dt.datetime.strftime(dt.datetime.today(), "%Y-%m-%d")
    return dt.datetime.strftime(d, "%Y-%m-%d")


# TODO: get list of weeks from lambda_services.py
def generate_weeks_list(sensor_info_dict: dict,
                        date_start: Union[str, None] = None):
    """Return list of dates to iterate through for sensor downloading.

    Will return dates for the sunday in each week. If date_start = None, then
    will return dates from the beginning of the sensor data until today.
    """
    if date_start is None:
        date_start = dt.datetime.utcfromtimestamp(sensor_info_dict['date_created'])
    else:
        date_start = dt.datetime.strptime(date_start, '%Y-%m-%d')
    date_start = date_start.date()
    date_list = pd.date_range(date_start, dt.datetime.today(), freq='w')
    if len(date_list) == 1:  #
        return date_list.append(pd.date_range(dt.datetime.today().date(), dt.datetime.today().date(), freq='d'))
    else:
        return date_list


def upload_file(file_path, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_path: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_path)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_path, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def lambda_pa_s3_writer(params, lambda_context):
    """
    Accepts an action and a number, performs the specified action on the number,
    and returns the result.

    :param params: dict of dict that contains the parameters sent when the function
                  is invoked.
    :param lambda_context: The context in which the function is called. Not used,
                           but required by Boto3-AWS-Lambda-client.invoke()
    :return: The result of the specified action.
    """
    sensor_id = params['sensor_id']
    bucket = params['bucket_name']
    start_date = params['start_date']
    PA_api_key = params['PA_api_key']
    end_date = add_six_months(start_date)

    # Create filename
    year = dt.datetime.strptime(start_date, "%Y-%m-%d").year
    month_start = dt.datetime.strptime(start_date, "%Y-%m-%d").month
    month_end = dt.datetime.strptime(end_date, "%Y-%m-%d").month
    filename = 'sensor_csvs' + f'/{sensor_id}_{year}_{month_start}-{month_end}.csv'
    logger.info(f'Sensor: {sensor_id},   Start: {year}-{month_start}')

    # Download data to CSV

    # Upload CSV to S3

    # Result
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

- Would like to figure out easy way of including pandas (and requests?)
https://duckduckgo.com/?q=python+write+txt+file+in+memory+io.StringIO&t=newext

- Need to remove pandas dependency:
    - Need to pass list of weeks to lambda function
    - write json files directly to S3 instead of turning to csvs
    - write IP test to txt using io.StringIO

"""
################################################################################
# Archive
################################################################################

def lambda_ip_s3_writer(params, lambda_context):
    """
    Accepts an action and a number, performs the specified action on the number,
    and returns the result.

    :param params: dict of dict that contains the parameters sent when the function
                  is invoked.
    :param lambda_context: The context in which the function is called. Not used,
                           but required by Boto3-AWS-Lambda-client.invoke()
    :return: The result of the specified action.
    """
    id_ = params['sensor_id']
    # id_list = params['sensor_id_list']
    bucket = params['bucket_name']
    start_date = params['start_date']
    end_date = params['end_date']


    weeks_list
    filename = 'sensor_csvs' + f'/{id_}.csv'
    logger.info(f'Sensor: {id_}')
    result = 'Success'
    # result = "Success" if ip_test(id_, bucket) else "Failure"
    logger.info(f'Result of uploading IP CSV: {result}')

    # result = download_sensor(id_, params['date_created'], params['date_end'])
    # result = ACTIONS[event['action']](event['number'])
    # logger.info('Calculated result of %s', result)

    response = {'result': result}
    return response
