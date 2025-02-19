import RPi.GPIO as GPIO
import time
import mysql.connector
from datetime import datetime

# GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

# Set GPIO Pins
STATION_1 = 2
STATION_2 = 3
STATION_3 = 4

# Keep track of previous station states so we don't double-trigger
# None indicates we haven't recorded a state yet.
station_states = {
    STATION_1: None,
    STATION_2: None,
    STATION_3: None
}

# Set GPIO direction (IN / OUT)
GPIO.setup(STATION_1, GPIO.IN)
GPIO.setup(STATION_2, GPIO.IN)
GPIO.setup(STATION_3, GPIO.IN)

def update_train_status(current_station, direction):
    try:
        connection = mysql.connector.connect(
            host='localhost',  # Change if needed
            user='root',  # Replace with your DB username
            password='admin',  # Replace with your DB password
            database='bedan'  # Replace with your DB name
        )
        cursor = connection.cursor()
        
        # Update train_status table
        query = "UPDATE train_status SET current_station = %s, direction = %s, last_update_time = %s WHERE train_id = 1"
        cursor.execute(query, (current_station, direction, datetime.now()))
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"Database error: {e}")

# Callback function for station detection
def station_callback(channel):
    current_state = GPIO.input(channel)
    previous_state = station_states[channel]

    direction = "FORWARD"
    # If the state hasn't changed, do nothing (prevents double-trigger)
    if current_state == previous_state:
        return
    
    # Update the stored state
    station_states[channel] = current_state

    if current_state == GPIO.LOW:
        # Train is arriving (falling edge)
        if channel == STATION_1:
            print("Train ARRIVED at Station 1")
            detected_station = 1
            update_train_status(detected_station, direction)
        elif channel == STATION_2:
            print("Train ARRIVED at Station 2")
            detected_station = 2
            update_train_status(detected_station, direction)
        elif channel == STATION_3:
            print("Train ARRIVED at Station 3")
            detected_station = 3
            update_train_status(detected_station, direction)
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
