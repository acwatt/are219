#!/usr/bin/env python

"""Functions to download purple air data via their API"""

# Built-in Imports
import datetime as dt
import os
import logging
import time
import numpy as np

import json
import pandas as pd
import requests
from typing import Optional, Union
from pathlib import Path
import threading

# Third-party Imports
from ratelimiter import RateLimiter
from timezonefinder import TimezoneFinder

# Local imports
from ..utils.config import PATHS, PA
from ..analyze.maps import sensor_df_to_geo

logger = logging.getLogger(__name__)


# If retrieving data from multiple sensors at once, please send a single request
# rather than individual requests in succession.


################################################################################
# HELPER FUNCTIONS
################################################################################
def parse_json(json_):
    dict_ = json.loads(json_)
    return


def rest_csv_to_df(url, query):
    """Return REST query from API."""
    logger.info(f'Making the following request from {url}')
    logger.info(query)
    response = requests.get(url, params=query)
    data = response.json()
    logger.info(f'Request {"successful" if response.status_code else "failed"}')
    df = pd.DataFrame(data['data'], columns=data['fields'])
    return df


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


def get_sensor_timezone(info):
    """Return timezone of sensor located at lat,lon decimal coordinates."""
    lat, lon = info['latitude'], info['longitude']
    obj = TimezoneFinder()
    timezone = obj.timezone_at(lng=lon, lat=lat)
    return timezone


# def filter_data(df):
#     df = (df.query('location_type == "outside"')
#           .query('downgraded == False')
#           .query('flagged == False')
#           )
#     return df


def filter_data(gdf):
    gdf = (gdf
           .query('channel_state == 3')
           .query('channel_flags == 0')
           .query('confidence_auto > 75')
           .query('position_rating > 1'))
    return gdf


################################################################################
# PURPLE AIR FUNCTIONS
################################################################################
def pa_request_single_sensor(sensor_id):
    api_key = PA.read_key
    url = f'https://api.purpleair.com/v1/sensors/{sensor_id}'
    fields = 'name, date_created, last_modified, latitude, longitude, position_rating, ' \
             'pm2.5, primary_id_a, primary_key_a, secondary_id_a, secondary_key_a, ' \
             'primary_id_b, primary_key_b, secondary_id_b, secondary_key_b'
    query = {'api_key': api_key, 'fields': fields.replace(' ', '')}
    response = requests.get(url, params=query)
    return response.json()


def dl_sensor_list_latlon_extent():
    """Download sensor metadata for california"""
    api_key = PA.read_key
    url = "https://api.purpleair.com/v1/sensors"
    fields = "sensor_index,date_created,latitude,longitude,altitude,position_rating," \
             "private,location_type,confidence_auto,channel_state,channel_flags," \
             "primary_id_a, primary_key_a, secondary_id_a, secondary_key_a, " \
             "primary_id_b, primary_key_b, secondary_id_b, secondary_key_b," \
             "pm2.5,pm2.5_a,pm2.5_b,pm2.5_24hour,pm2.5_1week," \
             "humidity,temperature,pressure,voc,ozone1"
    query = {'api_key': api_key, 'fields': fields.replace(" ", ""),
             "location_type": "0", "max_age": "0",
             "nwlng": "-124.96724575090495", "nwlat": "42.270281433624675",
             "selng": "-112.18776576411574", "selat": "28.080798371749676"}
    response = requests.get(url, params=query)


def dl_sensor_list_all():
    """Download add PurpleAir sensors' metadata."""
    api_key = PA.read_key
    url = "https://api.purpleair.com/v1/sensors"
    fields = "sensor_index,date_created,latitude,longitude,altitude,position_rating," \
             "private,location_type,confidence_auto,channel_state,channel_flags," \
             "primary_id_a, primary_key_a, secondary_id_a, secondary_key_a, " \
             "primary_id_b, primary_key_b, secondary_id_b, secondary_key_b"
    query = {'api_key': api_key, 'fields': fields.replace(" ", ""),
             "location_type": "0", "max_age": "0"}
    df = rest_csv_to_df(url, query)
    # Convert unix date to datetime
    # df = df.assign(date_start=dt.datetime.utcfromtimestamp(df['date_created']))
    df['date_created'] = df.apply(lambda row: dt.datetime.utcfromtimestamp(row['date_created']), axis=1)
    return df


def dl_sensor_list_in_geography(extent: str='US',
                                save_dir: Path=Path('/tmp/purple_air_data')):
    """Filter out sensors outside of extent (drop sensors outside US).

    @param extent: str, geographical extent to filter to.
        Allowed: 'world', 'us', 'california'
    @param save_dir: pathlib path of directory to save CSV to. Pass None
        if no CSV should be saved.
    @return gdf: geodataframe with only sensors inside of extent
    """
    logger.info('Getting metadata for all Purple Air sensors')
    df = dl_sensor_list_all()
    df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
    logger.info(f'Total number of sensors: {len(df)}')
    print("# of world Purple Air sensors:", len(df))
    logger.info(f'Filtering out sensors outside of {extent.upper()}')
    gdf, _ = sensor_df_to_geo(df, area=extent)
    logger.info(f'Number of sensors after geographical filtering: {len(gdf)}')
    if save_dir is not None:
        gdf.to_csv(save_dir / f'sensor_lookup_{extent}.csv')
    return gdf


def make_data_dir():
    dir_ = "/tmp/purple_air_data"
    if not(os.path.isdir(dir_)):  # doesn't exist
        os.mkdir(dir_)
    return dir_


################################################################################
# THINGSPEAK FUNCTIONS
################################################################################
# @RateLimiter(max_calls=1, period=1)
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
    response = requests.get(url, params=query_str)
    columns = {key: response.json()['channel'][key] for key in [f'field{k}' for k in range(1, 9)]}
    df = (pd.DataFrame(response.json()['feeds'])
          .rename(columns=columns))
    return df


def ts_example():
    sensor_info = pa_request_single_sensor(25999)['sensor']
    date_list = generate_weeks_list(sensor_info)
    for d in date_list: print(d)

    channel_id = sensor_info['primary_id_a']
    api_key = sensor_info['primary_key_a']
    start_date = dt.datetime.today().date() - dt.timedelta(days=20)
    end_date = start_date + dt.timedelta(days=7)
    timezone = get_sensor_timezone(sensor_info)
    df = ts_request(channel_id, start_date, api_key,
                    end_date=end_date, average=60, timezone=timezone)
    start_date = end_date
    end_date = start_date + dt.timedelta(days=7)
    timezone = get_sensor_timezone(sensor_info)
    df2 = ts_request(channel_id, start_date, api_key,
                     end_date=end_date, average=60, timezone=timezone)
    print(df.head())
    print(df.tail())
    print(df2.head())
    return df


def dl_sensor_week(sensor_info: dict, date_start: dt.datetime,
                   average: int = 60):
    """Download a week's (hourly) averages of data for sensor from all 4 channels.

    @param sensor_info: information about sensor
    @param date_start: date to start downloading from, with the 6 days following
    @param average: number of minutes to average over
    """
    date_end = date_start + dt.timedelta(days=7)
    timezone = get_sensor_timezone(sensor_info)

    print(sensor_info['sensor_index'], date_start.strftime('%Y-%m-%d'))
    logging.info(f"\n. . Downloading week {date_start.strftime('%Y-%m-%d')}")
    logging.info(f'. . Date Range: {date_start} - {date_end}')
    df_list = []
    # Iterate through the different channels of the device to get all the data
    for channel in ['a', 'b']:
        logging.info(f'. . . . channel {channel}: ')
        for type_ in ['primary', 'secondary']:
            channel_id = sensor_info[f'{type_}_id_{channel}']
            api_key = sensor_info[f'{type_}_key_{channel}']
            # Error handling in the downloading process
            errors = 0
            while errors < 5:
                try:  # get the data
                    df = ts_request(channel_id, date_start, api_key,
                                    end_date=date_end, average=average, timezone=timezone)
                    break
                except ConnectionError:
                    print(f'ts_request failed. Trying again. Previous errors = {errors}')
                    errors += 1
            if errors == 5:
                print(f'Reached maximum tries for channel {channel}, type {type_}, date {date_start} - {date_end}.')
                print('Skipping')
            if len(df) > 0:
                df.insert(loc=1, column='sensor_id', value=sensor_info['sensor_index'])
                df.insert(loc=2, column='channel', value=channel)
                df.insert(loc=3, column='subchannel_type', value=type_)
                df_list.append(df)
                logging.info(f'. . . . . . type {type_} ({len(df)})')
            elif len(df) == 0:
                # if any of the channels are empty, the data isn't useful
                logging.info('NO DATA -- skipping')
                return None

    if len(df_list) > 0:
        df2 = pd.concat(df_list)
        logging.info(f'\n. . total rows:{len(df2)}')
        return df2
    else:
        return None


def dl_sensor_weeks(sensor_id: Union[str, int, float] = None,
                    date_start: Optional[str] = None,
                    average: Optional[int] = None):
    """Download all data for PurpleAir sensor, one week at a time, then concatenate.

    The API works by calling all raw datapoints in a date window, then calculating
    any averages we ask for. ThingsSpeak also has a rate limit of 1 call per second
    and a rows-per-call limit of 8000. Sometimes this timesout at above 6,000 rows,
    so I am using 1 week for each channel of 4 channels per device.
    This is <=5040 rows of 2-min datapoints for each call from each channel
    (a-primary, a-secondary, b-primary, b-secondary).
    When we call for hourly averages, ThingsSpeak first calls the 5040 2-min
    datapoints, then calculates an hourly average for each channel in the device,
    so I still must limit calls to 1 week even when asking for averages.
    Note that ts_requst() is decorated by a RateLimiter that prevents it from
    being called more than once per second.

    Flow of script:
    1. Get metadata about sensor from PurpleAir API
    2. Use location of sensor from (1) to get timezone of sensor
    3. Generate a list of Sunday dates to download the weeks for
    4a. Iterate through the Sundays,
    4b. Iterate through the 4 channels (a-primary, a-secondary, b-primary, b-secondary)
    4c. Download one week of data from each channel and add to dataframe
    4d. Add some metadata about the sensor and channel to the dataframe
    4e. Add dataframe to list of dataframes
    5. Concatenate all dataframes into one large dataframe

    Example usage:
    # For a single PurpleAir sensor (id = 25999)
    dl_sensor_weeks(sensor_id=25999, date_start='2021-10-26', average=60)
    # For a list of sensors
    sensors = [25999, 22751]
    dfs = [pad.dl_sensor_weeks(id_, date_start='2021-10-26') for id_ in sensors]
    df_total = pd.concat(dfs).sort_values('created_at')

    :param sensor_id: str, int, float: PurpleAir sensor ID.
    :param date_start: str: date that we should begin downloading data for. If
                            omitted, the created_date of the sensor will be used
                            as start date, so all historical data will be
                            downloaded (only including full Sun-Sat weeks)
    :param average: str: Get average of this many minutes,
                    valid values: 10, 15, 20, 30, 60, 240, 720, 1440 (this is daily)
    :return: pandas.DataFrame: concatenated data from sensors
    """
    # todo: use info['latitude'], lon, to update dataframe of sensor
    #       see load_current_sensor_data() and update_loc_lookup()
    sensor_info = pa_request_single_sensor(sensor_id)['sensor']
    week_starts = generate_weeks_list(sensor_info, date_start=date_start)
    # Time how long the downloading takes
    time1 = dt.datetime.now()
    df_list = []
    logging.info(f'\nDownloading all weeks for sensor {sensor_id} ===================')
    for start_date in week_starts:
        df_week = dl_sensor_week(sensor_info, start_date)
        if df_week is None:
            continue
        else:
            df_list.append(df_week)

    if len(df_list) > 0:
        df = pd.concat(df_list)
    else:
        df = None
    time_taken = dt.datetime.now() - time1
    print(f'total time: {time_taken}')
    return df, time_taken


def save_success(sensor_id, time_taken, write_lock):
    filepath = PATHS.data.purpleair / 'sensors_downloaded.csv'
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        df = pd.DataFrame({'sensor_id': sensor_id, 'time_taken': time_taken},
                          index=[sensor_id])
    with write_lock:
        df.to_csv(filepath, index=False)


def dl_sensors(sensor_list, write_lock):
    """Save data for each sensor to local CSV"""
    save_dir = make_data_dir()

    for sensor_id in sensor_list:
        df, time_taken = dl_sensor_weeks(sensor_id)
        df = df.sort_values(by=['created_at', 'sensor_id', 'channel', 'subchannel_type'])
        filepath = f'{save_dir}/{sensor_id:06d}.csv'
        df.to_csv(filepath)
        # Sensor done, write success to file
        save_success(sensor_id, time_taken, write_lock)


def dl_us_sensors():
    gdf = dl_sensor_list_in_geography('US')
    print("# of US Purple Air sensors:", len(gdf))
    gdf = filter_data(gdf)
    print("# of US Purple Air sensors after filtering:", len(gdf))
    # randomize the sensors and pick num_sensors to time
    np.random.seed(13)
    sensor_list = np.random.permutation(gdf.sensor_index)
    num_sensors = 5
    sensor_list = sensor_list[:num_sensors]
    write_lock = threading.Lock()
    times = []
    for num_threads in range(1, 6):
        start = time.perf_counter()
        sensor_lists = np.array_split(sensor_list, num_threads)
        threads = []
        for i in range(num_threads):
            s_list = sensor_lists[i]
            args = (s_list, write_lock)
            thread = threading.Thread(target=dl_sensors, args=args)
            thread.start()
            threads.append(thread)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        t = round((time.perf_counter() - start)/60, 2)
        print(f'TIME: {t} minutes')
        times.append([num_threads, t/num_sensors])

    print('Average times:')
    print(times)


def update_loc_lookup(df, output=False):
    """Update the location lookup table for sensor id's; return lookup if output=True."""
    loc_cols = ['id', 'lat', 'lon', 'date']
    try:
        loc_lookup = pd.read_csv(PATHS.data.lookup_location)
    except FileNotFoundError:
        loc_lookup = pd.DataFrame(columns=loc_cols)
    # Update lookup
    today = dt.today().date().strftime('%Y-%m-%d')
    loc_lookup = (loc_lookup.merge(df
                                   .reset_index()
                                   .filter(loc_cols, axis=1),
                                   how='outer',
                                   on=['id', 'lat', 'lon'])
                  .fillna({'date': today}))
    loc_lookup.to_csv(PATHS.data.lookup_location, index=False)
    if output:
        return loc_lookup


if __name__ == "__main__":
    """
    sensor_df = load_current_sensor_data()
    sensor_df2 = pd.concat([sensorid_to_df(id) for id in sensor_df.index[:21]])
    # Single sensor
    se = Sensor(int(sensor_df.index[0]))
    print(se)
    print(se.parent)
    print(se.child)
    print(se.parent.as_flat_dict())
    se.get_field(3)
    se.get_field(4)
    print(se.thingspeak_data.keys())
    df = se.parent.get_historical(weeks_to_get=1, thingspeak_field='primary')
    df2 = se.child.get_historical(weeks_to_get=1, thingspeak_field='p')
    df.created_at.groupby(df["created_at"].dt.date).count().plot(kind="bar")

    se2 = [Sensor(id) for id in sensor_df.index[:2]]
    se2 = []
    cols_to_keep = ['UptimeMinutes', 'ADC', 'Temperature_F', 'Humidity_%', 'PM2.5 (CF=ATM) ug/m3']
    dfs = [(se
            .parent
            .get_historical(weeks_to_get=1, thingspeak_field='primary')
            .assign(sensor_id=se.identifier, channel='parent')
            .filter(cols_to_keep, axis=1)) for se in se2]

    se.get_data()
    print(df.head())
    print(df.tail())
    """

################################################################################
# PURPLE AIR NETWORK PACKAGE FUNCTIONS (no longer in use)
################################################################################
"""
PURPLE AIR PYTHON LIBRARY: https://github.com/ReagentX/purple_air_api
Conditions of use:
 License and copyright notice
 State changes
 Disclose source
 Same license
"""


# import purpleair.network as pan
# from purpleair.network import SensorList, Sensor


def df_sensors():
    """Return list of sensors that have valid data."""
    p = pan.SensorList()  # Initialized 22,877 sensors!22,836
    # Other sensor filters include 'outside', 'all', 'useful', 'family', and 'no_child'
    df = p.to_dataframe(sensor_filter='outside', channel='parent')
    # TODO: Cache and check if this has already been downloaded in past 7 days
    #       if not, redownload and update the cache
    return df


def load_current_sensor_data(update_lookup=True):
    """Return dataframe of current sensor data."""
    df = df_sensors()
    df = filter_data(df)
    # Update sensor location lookup table
    if update_lookup:
        update_loc_lookup(df)
    return df


def dl_from_sensor(sensor_id, start_date=dt.datetime.now()):
    df = (pan.Sensor(sensor_id)
          .parent.get_historical(weeks_to_get=1,
                                 thingspeak_field='secondary',
                                 start_date=start_date))
    return df


def sensorid_to_df(sensor_id):
    """Return dataframe of current sensor data from sensor with id = sensor_id"""
    print(sensor_id)
    dict_ = Sensor(int(sensor_id)).as_dict()
    row_dict = {}
    for channel in dict_:
        suffix = {'parent': '_1', 'child': '_2'}[channel]
        for k1 in dict_[channel]:
            for k2 in dict_[channel][k1]:
                row_dict[k2 + suffix] = [dict_[channel][k1][k2]]
    # Add created datetime column
    created_unix = dict_['parent']['diagnostic']['created']
    return (pd.DataFrame.from_dict(row_dict)
            .assign(created_date=dt.utcfromtimestamp(created_unix)))


def dl_id_by_date(id, end_date, num_weeks=10):
    """Return dataframe of historical sensor data for id between dates."""
    dfs = [(se
            .parent
            .get_historical(weeks_to_get=1, thingspeak_field='primary')
            .assign(sensor_id=se.identifier, channel='parent')
            .filter(cols_to_keep, axis=1)) for se in se2]


################################################################################
# GENERAL ARCHIVE
################################################################################
def add_field_columns(df, channel, type_):
    # column names dictionary
    colnames_dict = {
        'primary_fields_a': ["created_at", "entry_id", "pm1_0_atm", "pm2_5_atm",
                             "pm10_0_atm", "uptime_min", "rssi_wifi_strength",
                             "temp_f", "humidity", "pm2_5_cf_1"],
        'secondary_fields_a': ["created_at", "entry_id", "p_0_3_um", "p_0_5_um",
                               "p_1_0_um", "p_2_5_um", "p_5_0_um", "p_10_0_um",
                               "pm1_0_cf_1", "pm10_0_cf_1"],
        'primary_fields_b': ["created_at", "entry_id", "pm1_0_atm", "pm2_5_atm",
                             "pm10_0_atm", "free_heap_memory", "analog_input",
                             "sensor_firmware_pressure", "not_used", "pm2_5_cf_1"],
        'secondary_fields_b': ["created_at", "entry_id", "p_0_3_um", "p_0_5_um",
                               "p_1_0_um", "p_2_5_um", "p_5_0_um", "p_10_0_um",
                               "pm1_0_cf_1", "pm10_0_cf_1"]
    }

    # Rename the columns
    df.columns = colnames_dict[f'{type_}_fields_{channel}']
    return df