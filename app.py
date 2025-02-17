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
    Continuously poll GPIO pins to detect station changes or repeated detections,
    then call handle_station_event(detected_station).
    Note: We do NOT filter out repeated 'detected_station == prev_station' 
          so we can finalize a maneuver if the sensor never untriggers.
    """
    try:
        while True:
            detected_station = None

            # Read pins (0 means "station triggered")
            if GPIO.input(STATION_1) == 0:
                detected_station = 1
            elif GPIO.input(STATION_2) == 0:
                detected_station = 2
            elif GPIO.input(STATION_3) == 0:
                detected_station = 3

            # If we detect a station, handle the event (even if it's the same as last time)
            if detected_station is not None:
                handle_station_event(detected_station)

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("GPIO polling stopped by user.")
    finally:
        GPIO.cleanup()

def handle_station_event(detected_station):
    """
    Core state-machine logic. We allow repeated detection of the same station 
    (i.e., we do NOT require station change to call update_speed or finalize maneuvers).
    """
    global current_station, current_state, direction, last_update_time, current_speed
    global maneuver_start_time
    global station_timestamps

    arrival_time = datetime.now()
    last_update_time = arrival_time

    # We'll reference a "prev_station" for speed updates or direction changes
    # But it won't prevent us from handling repeated station triggers.
    prev_stn = current_station

    # -------------------------------------------
    # STATE MACHINE
    # -------------------------------------------
    if current_state == RUNNING:
        # Update direction/speed ONLY if station actually changed
        if prev_stn is not None and prev_stn != detected_station:
            if prev_stn < detected_station:
                direction = "FORWARD"
            else:
                direction = "BACKWARD"
            update_speed(prev_stn, detected_station, arrival_time)

        current_station = detected_station

        # Check if we triggered a maneuver:
        # 1) Arrive at station 1 from station 2, going BACKWARD
        if (detected_station == 1 and prev_stn == 2 and direction == "BACKWARD"):
            current_state = MANEUVERING_1
            maneuver_start_time = arrival_time
            print("[GPIO] *** Starting Maneuver at Station 1 ***")

        # 2) Arrive at station 3 from station 2, going FORWARD
        elif (detected_station == 3 and prev_stn == 2 and direction == "FORWARD"):
            current_state = MANEUVERING_3
            maneuver_start_time = arrival_time
            print("[GPIO] *** Starting Maneuver at Station 3 ***")

    elif current_state == MANEUVERING_3:
        # We'll consider the maneuver DONE the *next* time we see Station 3, 
        # provided we "left" it at least once. We'll do that check:
        # if detected_station == 3 and prev_stn != 3 => finalize
        if detected_station == 3 and prev_stn != 3:
            current_state = MANEUVERING_DONE
            print("[GPIO] *** Maneuver at Station 3 Complete! ***")

        current_station = detected_station

    elif current_state == MANEUVERING_1:
        # Similarly, for station 1
        if detected_station == 1 and prev_stn != 1:
            current_state = MANEUVERING_DONE
            print("[GPIO] *** Maneuver at Station 1 Complete! ***")

        current_station = detected_station

    elif current_state == MANEUVERING_DONE:
        # Once we get here, we finalize direction
        if current_station == 1:
            direction = "FORWARD"
        elif current_station == 3:
            direction = "BACKWARD"

        current_state = RUNNING
        print(f"[GPIO] *** Exiting Maneuver: now RUNNING, direction={direction} ***")

        # If station truly changed, update speed
        if prev_stn is not None and prev_stn != detected_station:
            update_speed(prev_stn, detected_station, arrival_time)

        current_station = detected_station

    # Always update timestamp
    station_timestamps[detected_station] = arrival_time


def update_speed(prev_stn, curr_stn, arrival_time):
    """
    Compute train's speed_km_h based on time difference between stations.
    Only called if station actually changed (prev_stn != curr_stn).
    """
    global current_speed

    distance_km = None
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
    as JSON for the front-end.
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

# If you want to serve index.html from the same dir:
@app.route("/")
def index_page():
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    gpio_thread = threading.Thread(target=gpio_polling, daemon=True)
    gpio_thread.start()

    print("[FLASK] Starting server on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
