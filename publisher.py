import numpy as np
import paho.mqtt.client as mqtt
import sys
import threading
import time

trigger = -1    # Global variable for triggering a sensor event

# MQTT broker details
broker    = 'pldindustries.com'
port      = 1883
topic     = "/group05a"
client_id = "Group05a"
username  = 'app_client'
password  = 'app@1234'

# Sensor details
#
# If you want to add a new sensor, just add its name, lower limit, upper limit,
# time interval, fraction value of the correlation and number of decimal pionts
# to this list.
#
#          ( name,    low, high, interval, fraction, decimal)
sensors = [("temp01", 20,  40,     0,       0.8,       2   ),
           ("hum01",  20,  100,    4,       0.9,       0   ),
           ("gas01",  10,  30,     0,       0.8,       3   ),
           ("smo01",  50,  150,    2,       0.8,       3   ),
           ("sec01",  10,  30,     0,       0.8,       3   ),
           ("mot01",  10,  30,     0,       0.8,       3   ),
           ("pow01",  10,  30,     0,       0.8,       3   ),
           ("temp02", 10,  30,     2,       0.8,       3   ),
           ("hum02",  10,  30,     2,       0.8,       3   ),
           ("temp03", 10,  30,     2,       0.8,       3   )]

# Function to create a sensor

# name      = Name of the sensor
# low       = Lower limit of the output values
# high      = Upper limit of the output values
# interval  = Time interval to publish the values.
# fraction  = Correlation with previous value
# decimal   = Number of decimal points of the output value
def create_sensor(name, low, high, interval, fraction, decimal):
    try:
        if low > high:
            raise Exception("Error: Upper limit is lower than the Lower limit!")
        if interval < 0:
            raise Exception("Error: Interval cannot be negetive!")
        if fraction > 1:
            raise Exception("Error: Fraction cannot be greater than 1!")

        local_seed = seed       # This is used for psuedorandom number generation and event triggering
        if decimal == 0:        # Decimal = 0 means no decimal points
            decimal = None

        print("\nInitialized the sensor:", name, end = ".")
        if interval == 0:               # Interval = 0 means the event is not periodic
            print("  ->  Enter {} to trigger the sensor {}".format(local_seed, name), end = " ")
        value = (low + high)/2          # Initial value. This can be changed.
        subtopic = topic + "/" + name
        rng = np.random.default_rng(local_seed)   
              
        while 1:
            rand_num = rng.integers(low, high, size=1)
            value = round((fraction*value + (1-fraction)*rand_num[0]), decimal)
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
        print("Couldn't initialize the sensor:", name)

# Creating and connecting the MQTT broker
client = mqtt.Client(client_id)
client.username_pw_set(username, password)
print("connecting to broker: ", broker)
client.connect(broker)

# Initializing the sensors
seed = -1
for sensor in sensors:
    seed += 1
    t = threading.Thread(target=create_sensor, args=sensor)
    t.daemon = True
    t.start()
    time.sleep(0.2)

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