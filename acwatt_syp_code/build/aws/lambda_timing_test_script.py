# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Modified by Aaron Watt, Jan 2022

"""
PURPOSE:
Writes IP address used during lambda function execution to S3 bucket CSV.
"""
import logging
import time
import random

import pandas as pd
import datetime as dt
import requests
import os
import threading
from multiprocessing import Process, Pipe

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
LOG_LOCK = threading.Lock()
WRITE_LOCK = threading.Lock()


def get_ip():
    """Return public IP address. From https://pytutorial.com/python-get-public-ip"""
    endpoint = 'https://ipinfo.io/json'
    response = requests.get(endpoint, verify = True)

    if response.status_code != 200:
        return f'Error status code: {response.status_code}'
        exit()

    data = response.json()
    return data['ip']


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
    wait = sleep_random(None)
    response = {'result': wait}
    return response


def sleep_random(start_date, conn):
    wait = int(random.random() * 20)
    with LOG_LOCK:
        logger.info(f"Downloading start date: {start_date}")
        logger.info(f"lambda thread sleeping for {wait}")
    time.sleep(wait)
    conn.send([f'{start_date} waited {wait} seconds'])
    conn.close()
    return wait


def ts_request(channel_id, start_date, api_key,
               end_date=None, average=None, timezone=None):
    """Return dataframe of REST json data response for thingsspeak request.

    @param channel_id = id of the device to get data from
    @param start_date = datetime date
    @param api_key = api key for the specific device with id channel_id
    @param end_date = datetime date or None
    @param average: integer, number of minutes to average over. Valid values:
        valid values: 10, 15, 20, 30, 60, 240, 720, 1440 (this is daily)
    @param timezone: timezone object from tz, timezone of device to get+ the
        correct time.
    """
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"
    if end_date is None:
        end_date = start_date + dt.timedelta(days=7)
    query = {'api_key': api_key,
             'start': start_date.strftime("%Y-%m-%d%%20%H:%M:%S"),
             'end': end_date.strftime("%Y-%m-%d%%20%H:%M:%S")}
    if average is not None:
        query['average'] = average  # in minutes
    if timezone is not None:
        query['timezone'] = timezone
    query_str = "&".join("%s=%s" % (k, v) for k, v in query.items())
    status_code = 300
    wait_time = 0.5
    while status_code >= 300 and wait_time < 1000:
        response = requests.get(url, params=query_str)
        status_code = response.status_code
        m = f"Status code {status_code}, TS channel {channel_id}, {start_date.strftime('%Y-%m-%d')}. Waiting {wait_time}."
        if status_code >= 300:
            logger.info(m)
        time.sleep(wait_time)
        wait_time = wait_time*2

    if response.status_code >= 300:
        return None
    columns = {key: response.json()['channel'][key] for key in [f'field{k}' for k in range(1, 9)]}
    df = (pd.DataFrame(response.json()['feeds'])
          .rename(columns=columns))
    return df


def dl_sensor_week(sensor_info: dict, date_start: dt.datetime, params: dict,
                   connection, average: int = 60):
    """Download a week's (hourly) averages of data for sensor from all 4 channels.

    @param sensor_info: information about sensor
    @param date_start: date to start downloading from, with the 6 days following
    @param timezone: string of a datetime timezone to use for correcting the time
        of the datapoints being downloaded
    @param connection:
    @param average: number of minutes to average over
    """
    date_end = date_start + dt.timedelta(days=7)
    # with print_lock: print(date_start)

    df_list = []
    # Iterate through the different channels of the device to get all the data
    for channel in ['a', 'b']:
        for type_ in ['primary', 'secondary']:
            channel_id = sensor_info[f'{type_}_id_{channel}']
            api_key = sensor_info[f'{type_}_key_{channel}']
            # Error handling in the downloading process
            errors = 0; df = None;
            while errors < 5:
                try:  # get the data
                    df = ts_request(channel_id, date_start, api_key,
                                    end_date=date_end, average=average,
                                    timezone=params['timezone'])
                    if df is False:
                        return
                    break
                except ConnectionError or requests.exceptions.HTTPError:
                    print(f'ts_request failed. Trying again. Previous errors = {errors}')
                    time.sleep(0.1)
                    errors += 1
            if errors == 5:
                print(f'Reached maximum tries for channel {channel}, type {type_}, date {date_start} - {date_end}.')
                print('Skipping')
                continue
            if df is not None:
                if len(df) > 0:
                    df.insert(loc=1, column='sensor_id', value=sensor_info['sensor_index'])
                    df.insert(loc=2, column='channel', value=channel)
                    df.insert(loc=3, column='subchannel_type', value=type_)
                    # Drop any "unused" or "Unused" columns to prevent pd.concat error
                    for col in set([col for col in df.columns if col.lower() == "unused"]):
                        df = df.drop(col, axis=1)
                    df_list.append(df)
                else:  # if any of the channels are empty, the data isn't useful
                    return None
    sensor_id = sensor_info['sensor_index']
    if len(df_list) == 4:
        df2 = pd.concat(df_list, ignore_index=True)
        logger.info(f"{sensor_id:06d}: Finished {date_start.strftime('%Y-%m-%d')}")
        filepath = f"/tmp/{sensor_id:07d}_{date_start.strftime('%Y-%m-%d')}.csv"
        with WRITE_LOCK:
            df2.to_csv(filepath, index=False)
            # upload_file_(filepath, params['bucket_name'])
        return df2
    else:
        logger.info(f"{sensor_id:06d}: No data for {date_start.strftime('%Y-%m-%d')}")
        return None


def generate_weeks_list(sensor_info_dict: dict):
    """Return list of dates to iterate through for sensor downloading.

    Will return dates for the sunday in each week. If date_start = None, then
    will return dates from the beginning of the sensor data until today.
    """
    date_start = dt.datetime.utcfromtimestamp(sensor_info_dict['date_created'])
    date_start = date_start.date()
    date_end = dt.datetime.utcfromtimestamp(sensor_info_dict['last_seen'])
    date_end += dt.timedelta(days=1)
    date_end = date_end.date()
    date_list = pd.date_range(date_start, date_end, freq='w')
    if len(date_list) == 1:  #
        return date_list.append(pd.date_range(dt.datetime.today().date(), dt.datetime.today().date(), freq='d'))
    else:
        return date_list


def pa_request_single_sensor(sensor_id, pa_api_key):
    url = f'https://api.purpleair.com/v1/sensors/{sensor_id}'
    fields = 'name, date_created, last_seen, last_modified, latitude, longitude, position_rating, ' \
             'pm2.5, primary_id_a, primary_key_a, secondary_id_a, secondary_key_a, ' \
             'primary_id_b, primary_key_b, secondary_id_b, secondary_key_b'
    query = {'api_key': pa_api_key, 'fields': fields.replace(' ', '')}
    response = requests.get(url, params=query)
    return response.json()


def upload_file_(file_path, bucket, object_name=None):
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
    return response


def thread_test(p, lambda_context):
    sensor_id = int(p['sensor_id'])
    ip = get_ip()
    logger.info(f"{sensor_id}: Full test of PA download, concatenation, S3 upload ({ip}).")

    # Get info for sensor
    sensor_info = pa_request_single_sensor(sensor_id, p['PA_api_key'])['sensor']
    # Get list of dates
    week_starts = generate_weeks_list(sensor_info)
    # Iterate through list of dates
    processes = []
    parent_connections = []
    for start_date in week_starts:
        # create a pipe for communication
        parent_conn, child_conn = Pipe()
        parent_connections.append(parent_conn)
        # create the process, pass instance and connection
        # process = Process(target=sleep_random, args=(start_date.date(), child_conn))
        process = Process(target=dl_sensor_week, args=(sensor_info, start_date, p, child_conn))
        processes.append(process)

    # start all processes
    i = 0
    for process in processes:
        process.start()
        logger.info(f"{sensor_id:06d}: Starting the process for {week_starts[i].strftime('%Y-%m-%d')}")
        time.sleep(p['time_between_processes'])
        i += 1

    # make sure that all processes have finished
    for process in processes:
        process.join()

    df_list, successful = [], []
    for file in os.listdir("/tmp"):
        if file.endswith(".csv"):
            filepath = os.path.join("/tmp", file)
            df_list.append(pd.read_csv(filepath))
            week = file.split('_')[1].split('.')[0]
            successful.append(week)

    # Concatenate all dataframes
    df = pd.concat(df_list)
    df = df.sort_values(by=['created_at', 'sensor_id', 'channel', 'subchannel_type'])

    # Make wide (combine primary and secondary data from each channel)
    df = df.pivot_table(index=['created_at', 'channel', 'sensor_id'], columns='subchannel_type').reset_index()
    # Drop empty rows
    df = df.dropna(subset=[('PM2.5 (CF=1)', 'primary'), ('2.5um', 'secondary')])

    # Save dataframe to CSV
    filepath = f'/tmp/{sensor_id:07d}.csv'
    df.to_csv(filepath, index=False)

    # Upload dataframe to S3 bucket
    upload_file_(filepath, p['bucket_name'])

    # Delete files
    for file in os.listdir("/tmp"):
        if file.endswith(".csv"):
            filepath = os.path.join("/tmp", file)
            os.remove(filepath)

    return {'successful': successful,
            'sensor_id': sensor_id,
            'ip': ip}

