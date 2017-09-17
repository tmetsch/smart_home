
# "Smart" home

Some python code to run on your [raspberrypi](https://www.raspberrypi.org/) or 
similar to measure e.g. temperatures internally and externally. Makes use of 
[openweathermap](openweathermap.org) and DHT22 sensors for now.

The data is stored using a simple [SQLite](https://www.sqlite.org/) database 
and can be displayed in your browser using [Chart.js](http://www.chartjs.org/).

The web interface is very generic, it will figure out itself what data to 
display based on what is in the Database. Hence adding data from other sensors 
is simple: 

  1) write a class which derives from 
     [threading.Thread](https://docs.python.org/2/library/threading.html)
  2) use a *DbWrapper* object from the sense module to store your data. When 
     the first *insert* is called, it'll automatically create the table in the 
     database according to the first datapoints you provide in a *dict* format.
  3) Update the run_sensing.py script to make sure you start the 'sensing' :-).

## Configuration file

Make sure you add the following defaults.cfg file:

    [server]
    debug=INFO
    bind_host=0.0.0.0
    bind_port=8080
    ssl_key=key.pem
    ssl_cert=cert.pem
    # The following is actually really bad :-)
    username=foo
    password=bar
    
    [data]
    database=data.sqlite3
    timeslice=86400
    resample=5Min
    
    [indoor_sensor]
    sleep=300
    dht=22
    gpio=14
    
    [outdoor_sensor]
    sleep=600
    city_id=123
    app_id=123

To provide a minimal level of TLS create an openssl server key:

    $ openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365

To remove the password do:

    $ cp key.pem key.pem.org
    $ openssl rsa -in key.pem.org -out key.pem

## Run the sensors

To kick of all sensors run:

    $ python ./run_sensing.py

## Run the frontend

To start the web interface run:

    $ python ./run_me.py
    
Now you can visit the dashboard.
