#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# GPIO pins
STATION_1 = 2
STATION_2 = 3
STATION_3 = 4

# Shared variables
current_station = None
direction = "FORWARD"
last_update_time = None

# State machine states
RUNNING = "RUNNING"
MANEUVERING_1 = "MANEUVERING_1"  # Maneuver at Station 1
MANEUVERING_3 = "MANEUVERING_3"  # Maneuver at Station 3
MANEUVERING_DONE = "MANEUVERING_DONE"

current_state = RUNNING
maneuver_start_time = None

GPIO.setmode(GPIO.BCM)
GPIO.setup(STATION_1, GPIO.IN)
GPIO.setup(STATION_2, GPIO.IN)
GPIO.setup(STATION_3, GPIO.IN)

def gpio_polling():
    global current_station, direction, last_update_time
    global current_state, maneuver_start_time

    prev_station = None
    direction = "FORWARD"

    try:
        while True:
            detected_station = None

            # Read station pins (assume 0 = triggered)
            if GPIO.input(STATION_1) == 0:
                detected_station = 1
            elif GPIO.input(STATION_2) == 0:
                detected_station = 2
            elif GPIO.input(STATION_3) == 0:
                detected_station = 3

            if detected_station is not None and detected_station != prev_station:
                arrival_time = datetime.now()
                last_update_time = arrival_time

                if current_state == RUNNING:
                    # Normal forward/backward logic
                    if prev_station is not None:
                        if prev_station < detected_station:
                            direction = "FORWARD"
                        else:
                            direction = "BACKWARD"

                    current_station = detected_station

                    # Check for maneuver triggers:
                    # 1) Station 1 from Station 2 going BACKWARD => MANEUVER_1
                    if (detected_station == 1 
                        and prev_station == 2 
                        and direction == "BACKWARD"):
                        current_state = MANEUVERING_1
                        maneuver_start_time = arrival_time
                        print("[GPIO] *** Starting Maneuver at Station 1 ***")
                    
                    # 2) Station 3 from Station 2 going FORWARD => MANEUVER_3
                    elif (detected_station == 3 
                          and prev_station == 2
                          and direction == "FORWARD"):
                        current_state = MANEUVERING_3
                        maneuver_start_time = arrival_time
                        print("[GPIO] *** Starting Maneuver at Station 3 ***")

                    prev_station = detected_station

                elif current_state == MANEUVERING_1:
                    # We're in the midst of a Station 1 maneuver
                    # We expect the train to leave station 1 (no station), 
                    # then come back to station 1
                    if detected_station == 1 and prev_station is None:
                        # Train returned to station 1
                        current_state = MANEUVERING_DONE
                        print("[GPIO] *** Maneuver at Station 1 Complete! ***")

                    current_station = detected_station
                    prev_station = detected_station

                elif current_state == MANEUVERING_3:
                    # Similarly, if we are maneuvering at station 3
                    if detected_station == 3 and prev_station is None:
                        # Train returned to station 3
                        current_state = MANEUVERING_DONE
                        print("[GPIO] *** Maneuver at Station 3 Complete! ***")

                    current_station = detected_station
                    prev_station = detected_station

                elif current_state == MANEUVERING_DONE:
                    # At the end of the maneuver, we set direction 
                    # (which side we consider 'forward' after reversing is up to you)
                    if current_station == 1:
                        direction = "FORWARD"
                    elif current_station == 3:
                        direction = "BACKWARD"
                    
                    # Return to running
                    current_state = RUNNING
                    print(f"[GPIO] *** Exiting Maneuver: direction now {direction} ***")

                    current_station = detected_station
                    prev_station = detected_station

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("GPIO polling stopped by user.")
    finally:
        GPIO.cleanup()

@app.route("/currentStatus")
def get_current_status():
    """
    Return station, direction, and state as JSON.
    """
    return jsonify({
        "current_station": current_station,
        "direction": direction,
        "state": current_state,
        "last_update_time": last_update_time.strftime("%Y-%m-%d %H:%M:%S")
            if last_update_time else None
    })

if __name__ == "__main__":
    gpio_thread = threading.Thread(target=gpio_polling, daemon=True)
    gpio_thread.start()

    print("Starting Flask server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
