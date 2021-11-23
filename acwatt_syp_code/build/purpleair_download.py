#!/usr/bin/env python

"""Functions to download purple air data via their API"""

# Built-in Imports
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import pandas as pd
import requests
from io import StringIO

# Third-party Imports
from ratelimiter import RateLimiter
import purpleair.network as pan
from purpleair.network import SensorList, Sensor
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
    fields = 'name, latitude, longitude, pm2.5,primary_id_a, primary_key_a, secondary_id_a, secondary_key_a, primary_id_b, primary_key_b, secondary_id_b, secondary_key_b'
    query = {'api_key': api_key, 'fields': fields.replace(' ','')}
    response = requests.get(url, params=query)
    return response.json()


@RateLimiter(max_calls=1, period=1)
def ts_requst(channel_id, start_date, api_key, end_date=None):
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
    query_str = "&".join("%s=%s" % (k, v) for k, v in query.items())
    response = requests.get(url, params=query_str)
    columns = {key: response.json()['channel'][key] for key in [f'field{k}' for k in range(1,9)]}
    df = (pd.DataFrame(response.json()['feeds'])
          .rename(columns=columns))
    return df


def ts_example():
    channel_id = 655100
    api_key = '2E6LYRAOFLQWQMIH'
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"
    start_date = datetime.today() - timedelta(weeks=10)
    end_date = datetime.today()
    query = {'api_key': api_key,
             'start': start_date.strftime("%Y-%m-%d%%20%H:%M:%S"),
             'end': end_date.strftime("%Y-%m-%d%%20%H:%M:%S"),
             'average': 10}
    query_str = "&".join("%s=%s" % (k, v) for k, v in query.items())
    response = requests.get(url, params=query_str)
    columns = {key: response.json()['channel'][key] for key in [f'field{k}' for k in range(1, 9)]}
    df = (pd.DataFrame(response.json()['feeds'])
          .rename(columns=columns))
    print(df)
    print(sum(df['PM2.5 (CF=1)'].isna()))


def dl_sensor_list():
    """Download sensor metadata for california"""
    # api_key = PA.read_key  # TODO: use this
    api_key = '5498FF4F-1642-11EC-BAD6-42010A800017'
    url = "https://api.purpleair.com/v1/sensors"
    fields = "sensor_index,date_created,latitude,longitude,altitude,private,location_type,confidence_auto,channel_state,channel_flags,pm2.5,pm2.5_a,pm2.5_b,pm2.5_24hour,pm2.5_1week,humidity,temperature,pressure,voc,ozone1"
    query = {'api_key': api_key, 'fields': fields.replace(" ", ""),
             "location_type": "0", "max_age": "0",
             "nwlng": "-124.96724575090495", "nwlat": "42.270281433624675",
             "selng": "-112.18776576411574", "selat": "28.080798371749676"}
    response = requests.get(url, params=query)


def dl_sensor_week(sensor_id, start_date=None):
    sensor_list = [22751, 30755]
    # todo: use info['latitude'], lon, to update dataframe of sensor
    # iterate through all different channels of data for sensor
    df_list = []
    today = datetime.today()
    ealiest_created_date = datetime.strptime('2016-01-01', '%Y-%m-%d')
    ealiest_created_date = datetime.strptime('2021-11-20', '%Y-%m-%d')
    date_list = pd.date_range(ealiest_created_date, today-timedelta(days=1), freq='w')
    date_list = date_list.append(pd.date_range(today, today, freq='d'))
    time1 = datetime.now()
    for i in reversed(range(len(date_list)-1)):
        start, end = date_list[i: i+2]
        for sensor_id in sensor_list:
            info = pa_request(sensor_id)['sensor']
            for channel in ['a', 'b']:
                for type_ in ['primary', 'secondary']:
                    print(f'Downloading for sensor {sensor_id}, channel {channel}, type {type_}, date {start} - {end}')
                    channel_id = info[f'{type_}_id_{channel}']
                    api_key = info[f'{type_}_key_{channel}']
                    # Error handling in the downloading process
                    errors = 0
                    while errors < 5:
                        try:  # get the data
                            df = ts_requst(channel_id, start, api_key, end_date=end)
                            break
                        except:
                            print(f'ts_requst failed. Trying again. Previous errors = {errors}')
                            errors += 1
                    if errors == 5:
                        print(f'Reached maximum trys for channel {channel}, type {type_}, date {date}.')
                        print('Skipping')
                    if len(df) > 0:
                        df['channel'] = channel
                        df['subchannel_type'] = type_
                        df['sensor_id'] = sensor_id
                        df_list.append(df)

    df2 = pd.concat(df_list)
    time2 = datetime.now()
    print(f'total time: {time2 - time1}')


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


def dl_from_sensor(sensor_id, start_date=datetime.now()):
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
    rest_query()

    # sensor_df = load_current_sensor_data()
    # sensor_df2 = pd.concat([sensorid_to_df(id) for id in sensor_df.index[:21]])
    # # Single sensor
    # se = Sensor(int(sensor_df.index[0]))
    # print(se)
    # print(se.parent)
    # print(se.child)
    # print(se.parent.as_flat_dict())
    # se.get_field(3)
    # se.get_field(4)
    # print(se.thingspeak_data.keys())
    # df = se.parent.get_historical(weeks_to_get=1, thingspeak_field='primary')
    # df2 = se.child.get_historical(weeks_to_get=1, thingspeak_field='p')
    # df.created_at.groupby(df["created_at"].dt.date).count().plot(kind="bar")
    #
    # se2 = [Sensor(id) for id in sensor_df.index[:2]]
    # se2 = []
    # cols_to_keep = ['UptimeMinutes', 'ADC', 'Temperature_F', 'Humidity_%', 'PM2.5 (CF=ATM) ug/m3']
    # dfs = [(se
    #         .parent
    #         .get_historical(weeks_to_get=1, thingspeak_field='primary')
    #         .assign(sensor_id=se.identifier, channel='parent')
    #         .filter(cols_to_keep, axis=1)) for se in se2]
    #
    # se.get_data()
    # print(df.head())
    # print(df.tail())
