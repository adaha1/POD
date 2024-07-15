#!/usr/bin/python3.9.6

import RPi.GPIO as GPIO
import time
import board
import busio
from adafruit_ads1x15 import ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from datetime import datetime
import csv

# Set channel to pin number for BOARD
#InflateChannel = 33
#DeflateChannel = 32
#ValveChannel = 13

# Set channel to socket code (GPIO21) for BCM
InflateChannel = 13
DeflateChannel = 12
ValveChannel = 27

### GPIO setup ###
# BOARD chooses channels by printed numbers on RPi, i.e. 40
#GPIO.setmode(GPIO.BOARD)

# BCM chooses channels by Broadcom SOC channel, i.e. GPIO21
# This project uses a module that sets mode for BCM. No other format is possible.
GPIO.setmode(GPIO.BCM)

GPIO.setup(InflateChannel, GPIO.OUT)
GPIO.setup(DeflateChannel, GPIO.OUT)
GPIO.setup(ValveChannel, GPIO.OUT)



### ADC Control Functions ###
# Guide - https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
# ADS gain is not used, so it is set to the default of 1
ads.gain = 1

# ADS mode set to single stream
ads.mode = ADS.Mode.SINGLE
# Offset is calculated at initialization to determine OpAmp bias
ads_offset = AnalogIn(ads, ADS.P0).voltage



### Data Logging ###
# 2 dimensional array that stores device activity for debugging
activity_log = [['Time', 'Object', 'Activity', 'Details']]


### File Handling ###
class FileHandler:
    # Data source indicates what generated the data being written to the file.
    # Default is set to pressure
    def __init__(self, data_source: str = "Log_") -> None:
        # File name is source + current time (YYYY-MM-DD_HH_mm_ss)
        # ex. "pressure_2023-2-19_11-32-55.csv"
        self.__file_name = data_source + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    
    def write_session(self, output: list[list]) -> None:
        with open(self.__file_name, 'w') as file:
            writer = csv.writer(file)
            for row in output:
                writer.writerow(row)

    def read_file(self):
        with open(self.__file_name, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                print('#' + str(reader.line_num) + ' ' + str(row))



### Flow Control State Machines ###
# FlowObject holds the logic for enabling and disabling the pumps and valves
class FlowObject:
    
    # When creating a FlowObject, the corresponding pin must be passed.
    def __init__(self, pin: int, name: str) -> None:
        # Input: int (Pin number), str (name of FlowObject)
        # Return: None
        self.__state = False # False = OFF/OPEN, True = ON/CLOSED
        self.__pin = pin
        self.__name = name

    # Set the desired state of the pump or valve
    def set_state(self, state: bool) -> None:
        # Input: boolean (flow state)
        # Return: None
        self.__state = state
        self.set_action()

    # Get the current state of the pump or valve
    def get_state(self) -> bool:
        # Input: None
        # Return: boolean (current flow state)
        return self.__state

    # Apply the current state to the pump or valve
    def set_action(self) -> None:
        # Input: None
        # Return: None
        if not self.__state:
            GPIO.output(self.__pin, GPIO.LOW)
            activity_log.append([datetime.now().strftime("%H:%M:%S"), "Turn off " + self.__name])
        else:
            GPIO.output(self.__pin, GPIO.HIGH)
            activity_log.append([datetime.now().strftime("%H:%M:%S"), "Turn on " + self.__name])

# Define the inflation, deflation, and valve as FlowObject state machines
# Control pin number and object name are passed to create the state machines
inflation_pump = FlowObject(InflateChannel, 'inflation_pump')
deflation_pump = FlowObject(DeflateChannel, 'deflation_pump')
valve = FlowObject(ValveChannel, 'valve')



### Testing/Manual Runs ###
if __name__ == '__main__':
    try:
        desired_number_of_trials    = input_sanitizer(input("Please enter how many trials to run:"))
        desired_pressure            = input_sanitizer(input("Please enter the desired pressure in mmHg:"))
        desired_inflate_time        = input_sanitizer(input("Please enter inflation duration in seconds:"))
        desired_hold_time           = input_sanitizer(input("Please enter how long to hold the desired pressure in seconds:"))
        desired_deflate_time        = input_sanitizer(input("Please enter deflation duration in seconds:"))
        desired_time_between_trials = input_sanitizer(input("Please enter duration of time between trials in seconds:"))
        ### Enters user input to activity log ###
        activity_log.append([datetime.now().strftime("%H:%M:%S"), "Number of Trials", str(desired_number_of_trials)])
        activity_log.append([datetime.now().strftime("%H:%M:%S"), "Target Pressure", str(desired_pressure)])
        activity_log.append([datetime.now().strftime("%H:%M:%S"), "Desired inflate time", str(desired_inflate_time)])
        activity_log.append([datetime.now().strftime("%H:%M:%S"), "Desired hold time", str(desired_hold_time)])
        activity_log.append([datetime.now().strftime("%H:%M:%S"), "Desired deflate time", str(desired_deflate_time)])
        activity_log.append([datetime.now().strftime("%H:%M:%S"), "Time between Trials", str(desired_time_between_trials)])

        ## Total trial time equation. 
        total_trial_time = desired_number_of_trials * (desired_inflate_time + desired_hold_time + desired_deflate_time) + (desired_time_between_trials * (desired_number_of_trials - 1))
        
        start_time = time.perf_counter()
        while (time.perf_counter() - start_time) < total_trial_time:            
            ## Inflation cycle. Starting time for inflation is recorded, and a function is called to compare current pressure
            ## to desired pressure at the current time. While loop keeps this running for as long as desired inflate time
            ## has not been reached
            inflate_start_time = time.perf_counter()
            while ((time.perf_counter() - desired_inflate_time - inflate_start_time) < 0):
                raise_pressure(inflation_line_pressure(desired_pressure, (time.perf_counter() - inflate_start_time), desired_inflate_time))
            
            activity_log.append([datetime.now().strftime("%H:%M:%S"), "Actual inflate time", str(time.perf_counter() - inflate_start_time)])

            ## While loop essentially waits the program for the hold time requested            
            hold_start_time = time.perf_counter()
            while ((time.perf_counter() - hold_start_time) < desired_hold_time):
                print("Holding at ", get_pressure())

            activity_log.append([datetime.now().strftime("%H:%M:%S"), "Actual hold time", str(time.perf_counter() - hold_start_time)])

            ## Deflation cycle. Essentially the same as inflation cycle            
            deflate_start_time = time.perf_counter()
            while ((time.perf_counter() - desired_deflate_time - deflate_start_time) < 0):
                lower_pressure(deflation_line_pressure(desired_pressure, deflate_start_time, desired_deflate_time))
            
            activity_log.append([datetime.now().strftime("%H:%M:%S"), "Actual deflate time", str(time.perf_counter() - deflate_start_time)])    
            
    except KeyboardInterrupt:
        emergency_shutoff()
        GPIO.cleanup()
        
    except:
        emergency_shutoff()
        GPIO.cleanup()

    emergency_shutoff()
    GPIO.cleanup()             

    log_file = FileHandler()
    log_file.write_session(activity_log)
    log_file.read_file()

### ADS Test : Deprecated
'''
def ADS_test():
    try:
        pump_on(InflateChannel)
        print(get_pressure())
        time.sleep(5)
        valve_open(ValveChannel)
        pump_off(InflateChannel)
        pump_on(DeflateChannel)
        print(get_pressure())
        time.sleep(5)
        pump_off(DeflateChannel)
        valve_close(ValveChannel)
        GPIO.cleanup()
    except KeyboardInterrupt:
        emergency_shutoff()
        GPIO.cleanup()
'''


### Pump Control Functions : Deprecated ###
'''
def pump_on(pin):
    GPIO.output(pin, GPIO.HIGH)

def pump_off(pin):
    GPIO.output(pin, GPIO.LOW)
    
def valve_open(pin):
    GPIO.output(pin, GPIO.HIGH)
    
def valve_close(pin):
    GPIO.output(pin, GPIO.LOW)

def emergency_shutoff(inflation_pin, deflation_pin, valve_pin):
    pump_off(inflation_pin)
    pump_off(deflation_pin)
    valve_open(valve_pin)
'''