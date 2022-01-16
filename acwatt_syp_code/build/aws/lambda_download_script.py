# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Modified by Aaron Watt, Jan 2022

"""
PURPOSE:
Writes IP address used during lambda function execution to S3 bucket CSV.
"""
import io
import logging
import pandas as pd
import datetime as dt
import requests
import json
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define a list of Python lambda functions that are called by this AWS Lambda function.

# TODO: get list of weeks from lambda_services.py
# def get_all_week_dates(date_beg, date_end):
#     #
#     date_list = pd.date_range(date_beg, date_end, freq='w')
#     pass
#
#
# def download_sensor_week(id_, week_beg, week_end):
#     # construct REST call to ThingsSpeak API
#
#     # Download JSON response
#
#     # Convert JSON to dataframe
#
#     pass
#
#
# def write_df_to_memcsv(df):
#     # Create CSV of df in memory
#
#     pass
#
#
# def upload_s3_csv(memcsv):
#     # Write fileobject to S3 bucket
#     pass
#
#
# def download_sensor(id_, date_beg, date_end):
#     # Get beginning and end dates of all weeks between creation and last modified
#     weeks_tuple_list = get_all_week_dates(date_beg, date_end)
#
#     # For each week
#     df_list = []
#     for week_beg, week_end in weeks_tuple_list:
#         # Download the Purple Air sensor data to dataframe
#         df_list.append(download_sensor_week(id_, week_beg, week_end))
#
#     # Write df to CSV in memory
#     df = pd.concat(df_list)
#     write_df_to_memcsv(df)
#
#     # Write S3 file
#     pass


def get_ip():
    """Return public IP address. From https://pytutorial.com/python-get-public-ip"""
    endpoint = 'https://ipinfo.io/json'
    response = requests.get(endpoint, verify = True)

    if response.status_code != 200:
        return f'Error status code: {response.status_code}'
        exit()

    data = response.json()
    return data['ip']


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


def ip_test(id_, bucket):
    ip = get_ip()
    df = pd.DataFrame({'ip': ip}, index=[id_])
    filepath = f'/tmp/{id_:06d}.csv'
    df.to_csv(filepath)
    # with open(filepath, 'w') as file:
    #     file.write(ip)
    # Save the IP address string to a file only in memory (not written to disk)
    # mem_csv = io.StringIO()
    # df.to_csv(mem_csv, index=False)
    # file.seek(0)  # need to set position of buffer back to begging before reading
    # Write CSV to S3 bucket (True/False for success/failure)
    return upload_file(filepath, bucket)


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
    bucket = params['bucket_name']
    created_date = params['date_created']
    last_modified = params['last_modified']
    filename = 'sensor_csvs' + f'/{id_}.csv'
    logger.info(f'Sensor: {id_}')

    result = "Success" if ip_test(id_, bucket) else "Failure"
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