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

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define a list of Python lambda functions that are called by this AWS Lambda function.

# TODO: get list of weeks from lambda_services.py


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
    id_list = params['sensor_id_list']
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