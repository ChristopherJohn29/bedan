# Libraries
import RPi.GPIO as GPIO
import time

# GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

# Set GPIO Pins
STATION_1 = 2
STATION_2 = 3
STATION_3 = 4

# Set GPIO direction (IN / OUT)
GPIO.setup(STATION_1, GPIO.IN)
GPIO.setup(STATION_2, GPIO.IN)
GPIO.setup(STATION_3, GPIO.IN)

# Callback function for station detection
def station_callback(channel):
    if channel == STATION_1:
        print("Station 1 detected!")
    elif channel == STATION_2:
        print("Station 2 detected!")
    elif channel == STATION_3:
        print("Station 3 detected!")

# Add event detection for each station
GPIO.add_event_detect(STATION_1, GPIO.FALLING, callback=station_callback, bouncetime=300)
GPIO.add_event_detect(STATION_2, GPIO.FALLING, callback=station_callback, bouncetime=300)
GPIO.add_event_detect(STATION_3, GPIO.FALLING, callback=station_callback, bouncetime=300)

if __name__ == '__main__':
    try:
        print("Waiting for station detection...")
        while True:
            # Keep the program running to detect events
            time.sleep(1)

    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()