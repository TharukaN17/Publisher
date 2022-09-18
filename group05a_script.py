# -------------------------------------------------------------------------------------------- #
### ---------------------------- IOT VIRTUAL SENSOR ENVIRONMENT ---------------------------- ###
# -------------------------------------------------------------------------------------------- #

import numpy as np
import paho.mqtt.client as mqtt
import sys
import threading
import time

# ------------------------------------------------------------------------------------------
# EDIT THIS SECTION AS YOUR REQUIREMENT
# ------------------------------------------------------------------------------------------

# MQTT broker details
broker    = 'pldindustries.com'
port      = 1883
topic     = "/group05a"
client_id = "Group05a"
username  = 'app_client'
password  = 'app@1234'

# Sensors using
#
# This contains the sensors that are using. If you want to use a sensor,
# just add a name and the sensor type/param list to this list.
# param list -> [low,high,interval,fraction,decimal]
#
#          (  name   , type/params)
sensors = [(  "co201", "co2"      ),
           ( "smo01" , "smoke"    ),
           ("pres01" , "pressure" ),
           ( "occ01" , "occupancy"),
           ( "cou01" , "counting" ),
           ( "lev01" , "level"    ),
           ( "cap01" , "capacity" ),
           (  "co202", [700,2000,30,0.7,0]),
           ("pres02" , "pressure" ),
           (  "lev02", [0,10,60,0.9,1])]

# Sensor details
#
# If you want to add a new sensor type, just add its type, lower limit, upper limit,
# time interval(s), fraction value of the correlation and number of decimal pionts
# to this dictionary. You can change sensor parameters by changing this.
#
#              { sensor_type : [low, high, interval, fraction, decimal]}
sensor_parms = {"co2"        : [400, 1000,   30,       0.7,       0   ],
                "smoke"      : [  1,    1,    0,         1,       0   ],
                "pressure"   : [ 90,  120,   30,       0.9,       2   ],
                "occupancy"  : [  1,    1,    0,         1,       0   ],
                "counting"   : [  0, 1000, 3600,         1,       0   ],
                "level"      : [  0,   20,   60,       0.9,       1   ],
                "capacity"   : [  0, 3000, 3600,       0.6,       1   ]}

# -----------------------------------------------------------------------------------------
# DO NOT EDIT THIS SECTION !!!
# -----------------------------------------------------------------------------------------

trigger = -1    # Global variable for triggering a sensor event

# Function to create a sensor
#
# name      = Name of the sensor
# low       = Lower limit of the output values
# high      = Upper limit of the output values
# interval  = Time interval to publish the values.
# fraction  = Correlation with previous value
# decimal   = Number of decimal points of the output value
def create_sensor(name, low, high, interval, fraction, decimal):
    try:
        if low > high:
            raise Exception("\n Error: Upper limit is lower than the Lower limit!")
        if interval < 0:
            raise Exception("\n Error: Interval cannot be negetive!")
        if fraction > 1:
            raise Exception("\n Error: Fraction cannot be greater than 1!")

        local_seed  = seed      # This is used for psuedorandom number generation and event triggering
        if decimal == 0:        # Decimal = 0 means no decimal points
            decimal = None

        print("\nInitialized the sensor:", name, end = ".")
        if interval == 0:                  # Interval = 0 means the event is not periodic
            print("  ->  Enter {} to trigger the sensor {}".format(local_seed, name), end = " ")
        value    = (low + high)/2          # Initial value. This can be changed.
        subtopic = topic + "/" + name
        rng      = np.random.default_rng(local_seed)   
              
        while 1:
            if low != high:
                rand_num = rng.integers(low, high, size=1)
            else:
                rand_num = [low]        # For binary outputs
            value    = round((fraction*value + (1-fraction)*rand_num[0]), decimal)
            # If the event is periodic
            if interval != 0:
                client.publish(subtopic, value)
                #print("Published {} to the topic {}".format(value, subtopic))
                time.sleep(interval)
            # If the event is not periodic
            else:
                global trigger
                if trigger == local_seed:
                    print("\n{} sensor Tiggered".format(name))
                    client.publish(subtopic, value)
                    #print("Published {} to the topic {}".format(value, subtopic))
                    trigger = -1
                
    except Exception as e:
        print("\n",e)
        print(" Couldn't initialize the sensor:", name)

# Creating and connecting the MQTT broker
client = mqtt.Client(client_id)
client.username_pw_set(username, password)
print("connecting to broker: ", broker)
client.connect(broker)

# Initializing the sensors
seed = -1
for sensor in sensors:
    try:
        seed += 1
        if not isinstance(sensor[0], str):
            raise Exception("\n Error: Sensor name should be a string!")

        # Creating the argument list
        if isinstance(sensor[1], str):
            if sensor[1] not in sensor_parms.keys():
                raise Exception("\n Error: Given sensor type'{}' is not available!".format(sensor[1]))  
            args = [sensor[0]] + sensor_parms[sensor[1]]
        elif isinstance(sensor[1], list):
            args = [sensor[0]] + sensor[1]
        else:
            raise Exception("\n Error: Given sensor type or parameters are not valid!")

        # Creating the thread
        t = threading.Thread(target=create_sensor, args=tuple(args))
        t.daemon = True
        t.start()
        time.sleep(0.2)
    except Exception as e:
        print("\n",e)
        print(" Couldn't initialize the sensor:", sensor[0])

# Waiting for quit command or event trigger command
while 1:
    time.sleep(0.5)
    try:
        code = int(input("\n\nEnter '-1' for exit:\n\n"))
        if code == -1:
            break
        else:
            trigger = code
    except Exception as e:
        print(e)

# Disconnecting and exiting
client.disconnect()
print("\nDisconnected from the broker")
time.sleep(0.5)
sys.exit()
