# Progress for 2022-01-05 report

## datetime convertion
 - needed to convert all PurpleAir data times from UTC to daylight-time specific timezones of the device
 - if a device is moved, the user is supposed to contact PurpleAir using their form to tell them it's moving. This allows for the old data to be kept with that sensor ID and all sensor ID's should only have one location. The user will then create a new sensor ID when placing their device again on the map. This relies on the good behavior of the device users, but currently no way to look at historical location -- only current lat-lon associated with each sensor.

