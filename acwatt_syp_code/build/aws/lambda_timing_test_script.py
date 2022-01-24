# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Modified by Aaron Watt, Jan 2022

"""
PURPOSE:
Writes IP address used during lambda function execution to S3 bucket CSV.
"""
import logging
import time

import pandas as pd
import datetime as dt
import requests
import os
import threading

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def time_test(params, lambda_context):
    """
    Accepts an action and a number, performs the specified action on the number,
    and returns the result.

    :param params: dict of dict that contains the parameters sent when the function
                  is invoked.
    :param lambda_context: The context in which the function is called. Not used,
                           but required by Boto3-AWS-Lambda-client.invoke()
    :return: The result of the specified action.
    """
    import random
    wait = int(random.random()*10)
    time.sleep(wait)

    response = {'result': wait}
    return response

