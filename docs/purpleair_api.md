

one of our main goals here at PurpleAir, to make high-quality data accessible to everyone. From elementary school students, to data scientists, people use our API to learn more about coding, API’s, geography, and especially air quality.

Your PurpleAir API keys are as follows:

- Read Key: 5498FF4F-1642-11EC-BAD6-42010A800017
- Write Key: 5499CF6C-1642-11EC-BAD6-42010A800017
- Documentation is available here: https://api.purpleair.com

You would need to use our API to get the thingspeak keys, for each sensor.  Then you would need to request data for each sensor individually from thingspeak. Since there are restrictions to the number of lines thingspeak returns in queries, you will need to perform multiple queries per sensor to get the period you are looking for then "stitch" all the data together.  

You can reference the api documentation at http://api.purpleair.com and also some information in the document linked at http://www.purpleair.com/sensorlist will help you some more.

Another way is to use the sensor list page:  https://www.purpleair.com/sensorlist   by clicking on the download link in the bottom right of the map. There is a drop down for the averages and you can select a date range and sensors you want data for.

Rate limiting is not something we anticipate having to do very often, if at all. To avoid this, and to maintain a high level of data availability (and reliability) for everyone, users can follow these general guidelines. 

The data from individual sensors will update no less than every 30 seconds. As a courtesy, we ask that you limit the number of requests to no more than once every 1 to 10 minutes, assuming you are only using the API to obtain data from sensors. If retrieving data from multiple sensors at once, please send a single request rather than individual requests in succession. 

PurpleAir’s API can be viewed here. If you would like to use our API, you can request an API key at this email address. Again, thank you for reaching out to us about this. Please let us know if you have any additional questions, and enjoy the rest of your week!


2021-11-09 query to web-api
read key: 5498FF4F-1642-11EC-BAD6-42010A800017
fields: sensor_index,date_created,latitude,longitude,altitude,private,location_type,confidence_auto,channel_state,channel_flags,pm2.5,pm2.5_a,pm2.5_b,pm2.5_24hour,pm2.5_1week,humidity,temperature,pressure,voc,ozone1
location_type: 0
max_age: 0
nwlng: 

nwlng: -124.96724575090495
nwlat: 42.270281433624675
selng: -112.18776576411574
selat: 28.080798371749676

GET https://api.purpleair.com/v1/sensors?fields=sensor_index%2Cdate_created%2Clatitude%2Clongitude%2Caltitude%2Cprivate%2Clocation_type%2Cconfidence_auto%2Cchannel_state%2Cchannel_flags%2Cpm2.5%2Cpm2.5_a%2Cpm2.5_b%2Cpm2.5_24hour%2Cpm2.5_1week%2Chumidity%2Ctemperature%2Cpressure%2Cvoc%2Cozone1&location_type=0&max_age=0&nwlng=-124.96724575090495&nwlat=42.270281433624675&selng=-112.18776576411574&selat=28.080798371749676 HTTP/1.1

X-API-Key: 5498FF4F-1642-11EC-BAD6-42010A800017


