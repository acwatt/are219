#!/usr/bin/env python

"""Functions to download purple air data via their API"""

# Built-in Imports
import datetime as dt
# from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import pandas as pd
import requests
from io import StringIO
from typing import Optional, Union
from pytz import timezone as tz

# Third-party Imports
from ratelimiter import RateLimiter
import purpleair.network as pan
from purpleair.network import SensorList, Sensor
from timezonefinder import TimezoneFinder

# Local imports
from ..utils.config import PATHS, PA


# If retrieving data from multiple sensors at once, please send a single request
# rather than individual requests in succession.


"""
PURPLE AIR PYTHON LIBRARY: https://github.com/ReagentX/purple_air_api
Conditions of use:
 License and copyright notice
 State changes
 Disclose source
 Same license
"""


def df_sensors():
    """Return list of sensors that have valid data."""
    p = pan.SensorList()  # Initialized 22,877 sensors!22,836
    # Other sensor filters include 'outside', 'all', 'useful', 'family', and 'no_child'
    df = p.to_dataframe(sensor_filter='useful', channel='parent')
    # TODO: Cache and check if this has already been downloaded in past 7 days
    #   if not, redownload and update the cache
    return df


def rest_csv_to_df(url, query):
    """Return REST query from API."""
    response = requests.get(url, params=query)
    df = pd.read_csv(StringIO(str(response.content)))
    return df


def pa_request(sensor_id):
    # api_key = PA.read_key  # TODO: use this
    api_key = '5498FF4F-1642-11EC-BAD6-42010A800017'
    url = f'https://api.purpleair.com/v1/sensors/{sensor_id}'
    fields = 'name, date_created, last_modified, latitude, longitude, position_rating, ' \
             'pm2.5, primary_id_a, primary_key_a, secondary_id_a, secondary_key_a, ' \
             'primary_id_b, primary_key_b, secondary_id_b, secondary_key_b'
    query = {'api_key': api_key, 'fields': fields.replace(' ', '')}
    response = requests.get(url, params=query)
    return response.json()


@RateLimiter(max_calls=1, period=1)
def ts_requst(channel_id, start_date, api_key,
              end_date=None, average=None, timezone=None):
    """Return dataframe of REST json data response for thingsspeak request.

    channel_id = id of the device to get data from
    start_date = datetime date
    api_key = api key for the specific device with id channel_id
    end_date = datetime date or None
    """
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"
    if end_date is None:
        end_date = start_date + timedelta(days=7)
        end_date = start_date + timedelta(minutes=4)
    query = {'api_key': api_key,
             'start': start_date.strftime("%Y-%m-%d%%20%H:%M:%S"),
             'end': end_date.strftime("%Y-%m-%d%%20%H:%M:%S")}
    if average is not None:
        query['average'] = average
    if timezone is not None:
        query['timezone'] = timezone
    query_str = "&".join("%s=%s" % (k, v) for k, v in query.items())
    response = requests.get(url, params=query_str)
    columns = {key: response.json()['channel'][key] for key in [f'field{k}' for k in range(1, 9)]}
    df = (pd.DataFrame(response.json()['feeds'])
          .rename(columns=columns))
    return df


def ts_example():
    channel_id = 655100
    api_key = '2E6LYRAOFLQWQMIH'
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"
    start_date = dt.datetime.today() - dt.timedelta(weeks=10)
    end_date = dt.datetime.today()
    query = {'api_key': api_key,
             'start': start_date.strftime("%Y-%m-%d%%20%H:%M:%S"),
             'end': end_date.strftime("%Y-%m-%d%%20%H:%M:%S"),
             'average': 10}
    query_str = "&".join("%s=%s" % (k, v) for k, v in query.items())
    response = requests.get(url, params=query_str)
    columns = {key: response.json()['channel'][key] for key in [f'field{k}' for k in range(1, 9)]}
    df = (pd.DataFrame(response.json()['feeds'])
          .rename(columns=columns))
    return df


def dl_sensor_list():
    """Download sensor metadata for california"""
    # api_key = PA.read_key  # TODO: use this
    api_key = '5498FF4F-1642-11EC-BAD6-42010A800017'
    url = "https://api.purpleair.com/v1/sensors"
    fields = "sensor_index,date_created,latitude,longitude,altitude,position_rating,private,location_type,confidence_auto,channel_state,channel_flags,pm2.5,pm2.5_a,pm2.5_b,pm2.5_24hour,pm2.5_1week,humidity,temperature,pressure,voc,ozone1"
    query = {'api_key': api_key, 'fields': fields.replace(" ", ""),
             "location_type": "0", "max_age": "0",
             "nwlng": "-124.96724575090495", "nwlat": "42.270281433624675",
             "selng": "-112.18776576411574", "selat": "28.080798371749676"}
    response = requests.get(url, params=query)


def generate_weeks_list(date_start: Union[str, None], sensor_info_dict: dict):
    """Return list of dates to iterate through for sensor downloading.

    Will return dates for the sunday in each week. If date_start = None, then
    will return dates from the beginning of the sensor data until today.
    """
    if date_start is None:
        date_start = dt.datetime.utcfromtimestamp(sensor_info_dict['date_created'])
    else:
        date_start = dt.datetime.strptime(date_start, '%Y-%m-%d')
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
    sensor_id = int(sensor_id)
    # todo: use info['latitude'], lon, to update dataframe of sensor
    #       see load_current_sensor_data() and update_loc_lookup()
    info = pa_request(sensor_id)['sensor']
    date_list = generate_weeks_list(date_start, info)
    timezone = get_sensor_timezone(info)
    # Time how long the downloading takes
    time1 = dt.datetime.now()
    # iterate through all different channels of data for sensor
    df_list = []
    print(f'\nDownloading for sensor {sensor_id}')
    for i in reversed(range(len(date_list)-1)):
        start, end = date_list[i: i+2].date
        # offset = daylight_savings_offset(start, timezone)
        print(f'. . Date Range: {start} - {end}')
        for channel in ['a', 'b']:
            for type_ in ['primary', 'secondary']:
                print(f'. . . . channel {channel}, type {type_}', end='   ')
                channel_id = info[f'{type_}_id_{channel}']
                api_key = info[f'{type_}_key_{channel}']
                # Error handling in the downloading process
                errors = 0
                while errors < 5:
                    try:  # get the data
                        df = ts_requst(channel_id, start, api_key,
                                       end_date=end, average=average, timezone=timezone)
                        break
                    except:
                        print(f'ts_requst failed. Trying again. Previous errors = {errors}')
                        errors += 1
                if errors == 5:
                    print(f'Reached maximum trys for channel {channel}, type {type_}, date {start} - {end}.')
                    print('Skipping')
                if len(df) > 0:
                    df['channel'] = channel
                    df['subchannel_type'] = type_
                    df['sensor_id'] = sensor_id
                    df_list.append(df)
                    print('Rows:', len(df))
        print('total rows:', len(pd.concat(df_list)))

    df2 = pd.concat(df_list)
    time2 = dt.datetime.now()
    print(f'total time: {time2 - time1}')
    return df2


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


def filter_data(df):
    df = (df.query('location_type == "outside"')
          .query('downgraded == False')
          .query('flagged == False')
          )
    return df


def dl_pm25(sensor_list):
    """Save dataframe of PM 2.5 data from all valid sensors."""
    for s in sensor_list:
        pass


def dl_from_sensor(sensor_id, start_date=dt.datetime.now()):
    df = (pan.Sensor(sensor_id)
          .parent.get_historical(weeks_to_get=1,
                                 thingspeak_field='secondary',
                                 start_date=start_date))
    return df


def dl_in_geo_area(gdf, start_date=None, num_weeks=None):
    """Download data from sensors in gdf between start_date and end_date.

    gdf = geopandas dataframe that has already been filtered for sensors within
        a geographic area using analyze.maps.sensor_df_to_geo()
    start_date, end_date = datetime.datetime date
    """
    # Request data from each sensor in num_week chunks
    beginning = datetime.today().date() - timedelta(weeks=num_weeks)
    # while beginning > start_date:
    #     for
    #
    #     beginning = beginning - timedelta(weeks=num_weeks)
    #     if beginning < start_date:
    #         beginning = start_date


def dl_id_by_date(id, end_date, num_weeks=10):
    """Return dataframe of historical sensor data for id between dates."""
    dfs = [(se
            .parent
            .get_historical(weeks_to_get=1, thingspeak_field='primary')
            .assign(sensor_id=se.identifier, channel='parent')
            .filter(cols_to_keep, axis=1)) for se in se2]


def dl_geo_by_date(gdf, start_date, end_date):
    """Download data from sensors in gdf between start_date and end_date.

    gdf = geopandas dataframe that has already been filtered for sensors within
        a geographic area using analyze.maps.sensor_df_to_geo()
    start_date, end_date = datetime.datetime date
    """
    pass


def sensorid_to_df(sensor_id):
    """Return dataframe of current sensor data from sensor with id = sensor_id"""
    print(sensor_id)
    dict_ = Sensor(int(sensor_id)).as_dict()
    row_dict = {}
    for channel in dict_:
        suffix = {'parent': '_1', 'child': '_2'}[channel]
        for k1 in dict_[channel]:
            for k2 in dict_[channel][k1]:
                row_dict[k2+suffix] = [dict_[channel][k1][k2]]
    # Add created datetime column
    created_unix = dict_['parent']['diagnostic']['created']
    return (pd.DataFrame.from_dict(row_dict)
          .assign(created_date=datetime.utcfromtimestamp(created_unix)))


def load_current_sensor_data(update_lookup=True):
    """Return dataframe of current sensor data."""
    df = df_sensors()
    df = filter_data(df)
    # Update sensor location lookup table
    if update_lookup:
        update_loc_lookup(df)
    return df


def update_loc_lookup(df, output=False):
    """Update the location lookup table for sensor id's; return lookup if output=True."""
    loc_cols = ['id', 'lat', 'lon', 'date']
    try:
        loc_lookup = pd.read_csv(PATHS.data.lookup_location)
    except FileNotFoundError:
        loc_lookup = pd.DataFrame(columns=loc_cols)
    # Update lookup
    today = datetime.today().date().strftime('%Y-%m-%d')
    loc_lookup = (loc_lookup.merge(df
                                   .reset_index()
                                   .filter(loc_cols, axis=1),
                                   how='outer',
                                   on=['id', 'lat', 'lon'])
                  .fillna({'date': today}))
    loc_lookup.to_csv(PATHS.data.lookup_location, index=False)
    if output:
        return loc_lookup


def parse_json(json_):
    dict_ = json.loads(json_)
    return


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
