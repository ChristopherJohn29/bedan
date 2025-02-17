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

    prev_station = 0
    current_station = 0
    direction = 'forward'

    try:
        while True:
            # --- Check STATION_1 ---
            if GPIO.input(STATION_1) == 0:
                current_station = 1
                if prev_station == 0:  # First detection
                    direction = 'forward'
                elif prev_station == 2:
                    direction = 'backward'
                prev_station = 1

            # --- Check STATION_2 ---
            elif GPIO.input(STATION_2) == 0:
                current_station = 2
                if prev_station == 1:
                    direction = 'forward'
                elif prev_station == 3:
                    direction = 'backward'
                prev_station = 2

            # --- Check STATION_3 ---
            elif GPIO.input(STATION_3) == 0:
                current_station = 3
                if prev_station == 0:  # First detection
                    direction = 'backward'
                elif prev_station == 2:
                    direction = 'forward'
                prev_station = 3
            
            # --- Check if no stations are triggered ---
            else:
                if prev_station == 1 and current_station == 1:
                    print("Train is maneuvering at Station 1")
                elif prev_station == 3 and current_station == 3:
                    print("Train is maneuvering at Station 3")
                else:
                    print(f"Train is moving {direction}")

            print(f"Current Position: {current_station}")
            print(f"Prev Position: {prev_station}")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()