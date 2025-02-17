#Libraries
import RPi.GPIO as GPIO
import time
 
#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
 
#set GPIO Pins
STATION_1 = 2
STATION_2 = 3
STATION_3 = 4
 
#set GPIO direction (IN / OUT)
GPIO.setup(STATION_1, GPIO.IN)
GPIO.setup(STATION_2, GPIO.IN)
GPIO.setup(STATION_3, GPIO.IN)
 
if __name__ == '__main__':

    prevSTATION_1 = 0
    prevSTATION_2 = 0
    prevSTATION_3 = 0

    try:
        while True:
            if GPIO.input(STATION_1) == 0:
                if prevSTATION_1 == 0:
                    prevSTATION_1 = 1
                    print ("STATION_1 Detected")
                    f = open("station1.txt", "w")
                    f.write("1")
                    f.close()                    
            else:
                if prevSTATION_1 == 1:
                    prevSTATION_1 = 0
                    print ("STATION_1 NOT Detected")
                    print ("STATION_1 Detected")
                    f = open("station1.txt", "w")
                    f.write("0")
                    f.close()                       

            if GPIO.input(STATION_2) == 0:
                if prevSTATION_2 == 0:
                    prevSTATION_2 = 1
                    print ("STATION_2 Detected")
                    f = open("station2.txt", "w")
                    f.write("1")
                    f.close()                                           
            else:
                if prevSTATION_2 == 1:
                    prevSTATION_2 = 0
                    print ("STATION_2 NOT Detected")                    
                    print ("STATION_2 Detected")
                    f = open("station2.txt", "w")
                    f.write("0")
                    f.close()                                                               

            if GPIO.input(STATION_3) == 0:
                if prevSTATION_3 == 0:
                    prevSTATION_3 = 1
                    print ("STATION_3 Detected")
                    print ("STATION_2 Detected")
                    f = open("station3.txt", "w")
                    f.write("1")
                    f.close()                                                               
            else:
                if prevSTATION_3 == 1:
                    prevSTATION_3 = 0
                    print ("STATION_3 NOT Detected")    
                    f = open("station3.txt", "w")
                    f.write("0")
                    f.close()                                                                                   

            time.sleep(.5)                

   # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
