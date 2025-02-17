#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

# -----------------------------
# GPIO PIN DEFINITIONS
# -----------------------------
STATION_1 = 2
STATION_2 = 3
STATION_3 = 4

# -----------------------------
# STATION DISTANCES (km)
# For speed calculation
# -----------------------------
DISTANCE_12 = 1.0   # Station 1 <-> Station 2
DISTANCE_23 = 1.0   # Station 2 <-> Station 3

# -----------------------------
# GLOBAL SHARED VARIABLES
# -----------------------------
current_station = None
direction = "FORWARD"
last_update_time = None
current_speed = 0.0  # in km/h

# We'll track station arrival timestamps
station_timestamps = {
    1: None,
    2: None,
    3: None
}

# -----------------------------
# STATE MACHINE
# -----------------------------
RUNNING = "RUNNING"
MANEUVERING_1 = "MANEUVERING_1"
MANEUVERING_3 = "MANEUVERING_3"
MANEUVERING_DONE = "MANEUVERING_DONE"

current_state = RUNNING
maneuver_start_time = None

# -----------------------------
# SETUP GPIO
# -----------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(STATION_1, GPIO.IN)
GPIO.setup(STATION_2, GPIO.IN)
GPIO.setup(STATION_3, GPIO.IN)

def gpio_polling():
    """
    Continuously poll GPIO pins to detect station changes, update:
      - current_station
      - direction
      - current_speed (based on timestamps & distance)
      - current_state (maneuvering logic)
    """
    global current_station, direction, last_update_time, current_speed
    global current_state, maneuver_start_time

    prev_station = None

    try:
        while True:
            detected_station = None

            # Read the pins (assuming 0 means "station triggered")
            if GPIO.input(STATION_1) == 0:
                detected_station = 1
            elif GPIO.input(STATION_2) == 0:
                detected_station = 2
            elif GPIO.input(STATION_3) == 0:
                detected_station = 3

            # If a new station is detected (different from the last loop)
            if detected_station is not None and detected_station != prev_station:
                arrival_time = datetime.now()
                last_update_time = arrival_time

                # -------------------------------------------
                # STATE MACHINE LOGIC
                # -------------------------------------------
                if current_state == RUNNING:
                    # Normal direction assignment
                    if prev_station is not None:
                        if prev_station < detected_station:
                            direction = "FORWARD"
                        else:
                            direction = "BACKWARD"

                    current_station = detected_station

                    # Calculate speed if we know the distance from prev_station->detected_station
                    if prev_station is not None:
                        update_speed(prev_station, detected_station, arrival_time)

                    # Check if we triggered a maneuver:
                    # 1) Arrive at station 1 from station 2 going BACKWARD
                    if (detected_station == 1
                        and prev_station == 2
                        and direction == "BACKWARD"):
                        current_state = MANEUVERING_1
                        maneuver_start_time = arrival_time
                        print("[GPIO] *** Starting Maneuver at Station 1 ***")

                    # 2) Arrive at station 3 from station 2 going FORWARD
                    elif (detected_station == 3
                          and prev_station == 2
                          and direction == "FORWARD"):
                        current_state = MANEUVERING_3
                        maneuver_start_time = arrival_time
                        print("[GPIO] *** Starting Maneuver at Station 3 ***")

                    # Record the timestamp
                    station_timestamps[detected_station] = arrival_time
                    prev_station = detected_station

                elif current_state == MANEUVERING_1:
                    # We are waiting for the train to leave station 1 and then come back
                    # Means: first the train might go "no station", then once it returns
                    # to station 1, we finalize the maneuver
                    if detected_station == 1 and prev_station is None:
                        # The train returned to station 1
                        current_state = MANEUVERING_DONE
                        print("[GPIO] *** Maneuver at Station 1 Complete! ***")

                    current_station = detected_station
                    # Possibly update speed if we want to measure movement in the yard
                    # but usually the yard track isn't an official 'station'
                    prev_station = detected_station

                elif current_state == MANEUVERING_3:
                    # Similar logic for station 3
                    if detected_station == 3 and prev_station is None:
                        current_state = MANEUVERING_DONE
                        print("[GPIO] *** Maneuver at Station 3 Complete! ***")

                    current_station = detected_station
                    prev_station = detected_station

                elif current_state == MANEUVERING_DONE:
                    # We finalize direction after the maneuver
                    if current_station == 1:
                        direction = "FORWARD"
                    elif current_station == 3:
                        direction = "BACKWARD"

                    current_state = RUNNING
                    print(f"[GPIO] *** Exiting Maneuver: now RUNNING, direction={direction} ***")

                    # Update speed if needed
                    if prev_station is not None:
                        update_speed(prev_station, detected_station, arrival_time)

                    station_timestamps[detected_station] = arrival_time
                    prev_station = detected_station

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("GPIO polling stopped by user.")
    finally:
        GPIO.cleanup()

def update_speed(prev_stn, curr_stn, arrival_time):
    """
    Compute the train's speed_km_h based on time difference between
    prev_stn -> curr_stn.
    """
    global current_speed

    distance_km = None
    # If route is 1->2 or 2->1
    if (prev_stn, curr_stn) in [(1,2), (2,1)]:
        distance_km = DISTANCE_12
    elif (prev_stn, curr_stn) in [(2,3), (3,2)]:
        distance_km = DISTANCE_23

    if distance_km is not None:
        prev_time = station_timestamps.get(prev_stn)
        if prev_time is not None:
            time_diff_sec = (arrival_time - prev_time).total_seconds()
            if time_diff_sec > 0:
                time_diff_hr = time_diff_sec / 3600.0
                speed_km_h = distance_km / time_diff_hr
                current_speed = round(speed_km_h, 2)
                print(f"[GPIO] Updated speed = {current_speed} km/h (from stn{prev_stn} to stn{curr_stn})")
            else:
                current_speed = 0.0
        else:
            current_speed = 0.0
    else:
        current_speed = 0.0

# ---------------------------------------------
# FLASK ENDPOINTS
# ---------------------------------------------
@app.route("/currentStatus")
def get_current_status():
    """
    Return current station, direction, state, last_update_time, and speed_km_h
    as JSON for the front-end to consume.
    """
    update_str = None
    if last_update_time:
        update_str = last_update_time.strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "current_station": current_station,
        "direction": direction,
        "state": current_state,
        "last_update_time": update_str,
        "speed_km_h": current_speed
    })

# Optional: Serve index.html if you want to serve the front-end from here
@app.route("/")
def index_page():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    gpio_thread = threading.Thread(target=gpio_polling, daemon=True)
    gpio_thread.start()

    print("[FLASK] Starting server on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
