#!/usr/bin/env python3

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
    """
    Updates the train_status row in the database with the given station & direction.
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',   # Adjust if needed
            user='root',        # Replace with your DB username
            password='admin',   # Replace with your DB password
            database='bedan'    # Replace with your DB name
        )
        cursor = connection.cursor()
        
        query = """
            UPDATE train_status
            SET current_station = %s, direction = %s, last_update_time = %s
            WHERE train_id = 1
        """
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
            
            # Check GPIO inputs (active-low or active-high depends on your wiring)
            # Here we assume "0" means "detected"
            if GPIO.input(STATION_1) == 0:
                detected_station = 1
            elif GPIO.input(STATION_2) == 0:
                detected_station = 2
            elif GPIO.input(STATION_3) == 0:
                detected_station = 3
            
            # If a station is detected and it's different from the previous station
            if detected_station is not None and detected_station != prev_station:
                
                # Determine direction (FORWARD or BACKWARD) based on previous vs. current
                if prev_station is not None:
                    if prev_station < detected_station:
                        direction = "FORWARD"
                    else:
                        direction = "BACKWARD"
                
                # --- Check for maneuver condition at Station 1 going BACKWARD ---
                if detected_station == 1 and direction == "BACKWARD":
                    print("Train arrived at Station 1 moving BACKWARD. Starting maneuver.")
                    
                    # 1) First, update the DB that we arrived at Station 1, BACKWARD
                    update_train_status(1, "BACKWARD")
                    
                    # 2) Update DB to show that we are "maneuvering"
                    update_train_status(1, "MANEUVERING")
                    
                    # 3) Simulate the maneuver time (5 seconds or 5 minutes, etc.)
                    time.sleep(5)  # or time.sleep(300) for 5 minutes
                    
                    # 4) After maneuver, you may want to switch direction to FORWARD
                    #    or remain BACKWARD depending on your operation
                    direction = "FORWARD"
                    update_train_status(1, direction)
                    
                    # Make station=1 the new 'previous station'
                    prev_station = 1
                    print("Maneuver at Station 1 complete. Direction now FORWARD.")
                
                else:
                    # Normal case: update DB with the detected station & direction
                    print(f"Train detected at STATION_{detected_station} moving {direction}")
                    update_train_status(detected_station, direction)
                    
                    prev_station = detected_station
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
