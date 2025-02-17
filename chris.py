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

if __name__ == '__main__':

    prevstation = 0
    currentstation = 0
    direction = 'forward'

    try:
        while True:
            # --- Check STATION_1 ---
            if GPIO.input(STATION_1) == 0:
                currentstation = 1
                if prevstation == 0:  # First detection
                    direction = 'forward'
                elif prevstation == 1:
                    direction = 'forward'
                else:
                    direction = 'forward'
                prevstation = 1

            # --- Check STATION_2 ---
            if GPIO.input(STATION_2) == 0:
                currentstation = 2
                if prevstation == 0:  # First detection
                    direction = 'forward'
                elif prevstation == 1:
                    direction = 'forward'
                else:
                    # If coming from station 3 => backward
                    direction = 'backward'
                prevstation = 2

            # --- Check STATION_3 ---
            if GPIO.input(STATION_3) == 0:
                currentstation = 3
                if prevstation == 0:  # First detection
                    direction = 'backward'
                elif prevstation == 3:
                    direction = 'backward'
                else:
                    direction = 'backward'
                prevstation = 3
            
            # --- Check if no stations are triggered ---
            if (GPIO.input(STATION_1) == 1 
                and GPIO.input(STATION_2) == 1 
                and GPIO.input(STATION_3) == 1):
                
                # Use currentstation (not current_station)
                if prevstation == 1 and currentstation == 1:
                    print("Train is maneuvering")
                elif prevstation == 3 and currentstation == 3:
                    print("Train is maneuvering")
                else:
                    print("Train is moving " + direction)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
