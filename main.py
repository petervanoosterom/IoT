import utime                  # Allows use of utime.sleep() for delays
import pycom                  
from umqtt import MQTTClient  # For use of MQTT protocol to talk to Adafruit IO
import machine
from machine import Pin
import ubinascii              # Needed to run any MicroPython code



##########################################################################
# Begin Configuration 
##########################################################################

# Water tank Parameters
TankHeight = 300      # Tank Height in cm
TankDiameter = 700    # Tank Diameter in cm

# Set up the Board reading ultrasonic sensor
echo = Pin(Pin.exp_board.G7, mode=Pin.IN) # Lopy4 specific: Pin('P20', mode=Pin.IN)
trigger = Pin(Pin.exp_board.G8, mode=Pin.OUT) # Lopy4 specific Pin('P21', mode=Pin.IN)
trigger(0)


# Configuration of MQTT Message Broker 
# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "UseYourAdafruitUsername"
AIO_KEY = "GetYourOwnAdaFruitKey"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # Can be anything
AIO_CONTROL_FEED = "vanjones/feeds/valvecontrol"
AIO_TANK_LEVEL_FEED = "vanjones/feeds/housewatertank"

##########################################################################
# End Configuration 
##########################################################################


##########################################################################
# Begin Functions
##########################################################################

# Caculate Tank Volumes 
def tank_volume(d,h): # Calculate the volume of the tank 
    PI = 3.1416
    radius = d / 2
    return (PI * radius * radius * h) / 1000 #Tank volume in litres 

# Ultrasonic distance measurment
def distance_measure():
    # trigger pulse LOW for 2us (just in case)
    trigger(0)
    utime.sleep_us(2)
    # trigger HIGH use 10us pulse for the HC-SR04, use 20us for JSN-SR04-v3
    trigger(1)
    utime.sleep_us(20)
    trigger(0)

    # wait for the rising edge of the echo then start timer
    while echo() == 0:
        pass
    start = utime.ticks_us()

    # wait for end of echo pulse then stop timer
    while echo() == 1:
        pass
    finish = utime.ticks_us()

    # pause for 20ms to prevent overlapping echos
    utime.sleep_ms(20)


    # calculate distance by using time difference between start and stop
    # speed of sound 340m/s or .034cm/us. Time * .034cm/us = Distance sound travelled there and back
    # divide by two for distance to object detected.
    distance = ((utime.ticks_diff(start, finish)) * .034)/2
    print (distance)
    
    return distance

# Function to respond to messages from Adafruit IO
def sub_cb(topic, msg):          # sub_cb means "callback subroutine"
    print((topic, msg))          # Outputs the message that was received. Debugging use.
    if msg == b"ON":             # If message says "ON" ...
        pycom.rgbled(0xffffff)   # ... then LED on
    elif msg == b"OFF":          # If message says "OFF" ...
        pycom.rgbled(0x000000)   # ... then LED off
    else:                        # If any other message is received ...
        print("Unknown message") # ... do nothing but output that it happened.


##########################################################################
# End Functions
##########################################################################


##########################################################################
# Main
##########################################################################


TotalVolume = tank_volume(TankDiameter, TankHeight)     # Total Tank volume


# RGBLED
# Disable the on-board heartbeat (blue flash every 4 seconds)
# We'll use the LED to respond to messages from Adafruit IO
pycom.heartbeat(False)
utime.sleep(0.1) # Workaround for a bug.
                # Above line is not actioned if another
                # process occurs immediately afterwards
pycom.rgbled(0xff0000)  # Status red = not working

# WIFI
# We need to have a connection to WiFi for Internet access
# wlan = WLAN(mode=WLAN.STA)
# wlan.connect(WIFI_SSID, auth=(WLAN.WPA2, WIFI_PASS), timeout=5000)

while not wlan.isconnected():    # Code waits here until WiFi connects
    machine.idle()

print("Connected to Wifi")
pycom.rgbled(0xffd7000) # Status orange: partially working

# Use the MQTT protocol to connect to Adafruit IO
client = MQTTClient(AIO_CLIENT_ID, AIO_SERVER, AIO_PORT, AIO_USER, AIO_KEY)

# Subscribed messages will be delivered to this callback
client.set_callback(sub_cb)
client.connect()
client.subscribe(AIO_CONTROL_FEED)
print("Connected to %s, subscribed to %s topic" % (AIO_SERVER, AIO_CONTROL_FEED))

pycom.rgbled(0x00ff00) # Status green: online to Adafruit IO


try:

    while True:
        distance_from_max = distance_measure()
        RemainingVolume = tank_volume(TankDiameter, (TankHeight + distance_from_max)) # This is a negative value hence addition
        Capacity = 100 * RemainingVolume / TotalVolume
        client.publish(topic=AIO_TANK_LEVEL_FEED, msg=str(Capacity))
        txt1 = "Remaining Volume: {:,.0f} litres".format(RemainingVolume)
        txt2 = "The Tank is at {:.1f}% Capacity".format(Capacity)
        print (txt1)
        print (txt2)
        utime.sleep(5)  # Sleep for 5 seconds, AIO account can only do 30 samples a minute, reality will do samle every 10 minutes 

finally:
    client.disconnect()          # ... disconnect the client and clean up.
    client = None
    # wlan.disconnect() # Don't mess with the wireless, still need to be able the device
    # wlan = None
    pycom.rgbled(0x000022)# Status blue: stopped
    print("Disconnected from Adafruit IO.")
