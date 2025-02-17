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
    if GPIO.input(channel) == GPIO.LOW:
        # Train is arriving (falling edge)
        if channel == STATION_1:
            print("Train ARRIVED at Station 1")
        elif channel == STATION_2:
            print("Train ARRIVED at Station 2")
        elif channel == STATION_3:
            print("Train ARRIVED at Station 3")
    else:
        # Train is leaving (rising edge)
        if channel == STATION_1:
            print("Train LEFT Station 1")
        elif channel == STATION_2:
            print("Train LEFT Station 2")
        elif channel == STATION_3:
            print("Train LEFT Station 3")

# Add event detection for each station (both rising and falling edges)
GPIO.add_event_detect(STATION_1, GPIO.BOTH, callback=station_callback, bouncetime=300)
GPIO.add_event_detect(STATION_2, GPIO.BOTH, callback=station_callback, bouncetime=300)
GPIO.add_event_detect(STATION_3, GPIO.BOTH, callback=station_callback, bouncetime=300)

if __name__ == '__main__':
    try:
        print("Waiting for station detection...")
        while True:
            # Keep the program running to detect events
            time.sleep(1)

    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()