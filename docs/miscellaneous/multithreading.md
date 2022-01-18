# Why use multithreading here?

[Quick examples of threading](https://www.pythontutorial.net/advanced-python/python-threading/)

[Good overview of threading vs multiprocessing vs concurrency vs subprocessing](https://docs.python.org/3/library/concurrency.html)

The major bottleneck in this project is downloading the data from Thingspeak.
This takes a while per request (about 1 second) and there are 4 requests per 
sensor-week. However, Thingspeak does not limit the number of requests we 
can make per second. 

By using multithreading in python, we can send a bunch of near simultaneous 
requests to Thingspeak without having to wait for each one to finish before 
sending the next. This is done by adding each REST request to a new thread 
(a new parallel process on our CPU). 

At the time of this writing, my Acer laptop from 2017 has roughly 62,000 
threads (using 
the terminal command `cat /proc/sys/kernel/threads-max`). So I can easily 
set number of threads fairly high and change my bottleneck from network 
request process speed to CPU speed or network bandwidth (which is a much 
larger bottleneck).