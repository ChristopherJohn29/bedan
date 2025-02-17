# Libraries
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

if __name__ == '__main__':
    prev_station = None
    direction = "FORWARD"
    try:
        while True:
            detected_station = None
            
            if GPIO.input(STATION_1) == 0:
                detected_station = 1
            elif GPIO.input(STATION_2) == 0:
                detected_station = 2
            elif GPIO.input(STATION_3) == 0:
                detected_station = 3
            
            if detected_station is not None and detected_station != prev_station:
                if prev_station is not None:
                    if prev_station < detected_station:
                        direction = "FORWARD"
                    else:
                        direction = "BACKWARD"
                
                print(f"Train detected at STATION_{detected_station} moving {direction}")
                update_train_status(detected_station, direction)
                prev_station = detected_station
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
