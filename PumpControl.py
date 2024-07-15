#!/usr/bin/python3.9.6
import RPi.GPIO as GPIO
import time
import board
import busio
from adafruit_ads1x15 import ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from datetime import datetime
import csv
import traceback

class PumpControl:
    def __init__(self,
                desired_number_of_trials: float,
                desired_pressure: float,
                desired_inflate_time: float,
                desired_hold_time: float,
                desired_deflate_time: float,
                desired_time_between_trials: float):

        ### Trial Settings ###
        GPIO.cleanup()
        self.desired_number_of_trials = desired_number_of_trials
        self.desired_pressure = desired_pressure
        self.desired_inflate_time = desired_inflate_time
        self.desired_hold_time = desired_hold_time
        self.desired_deflate_time = desired_deflate_time
        self.desired_time_between_trials = desired_time_between_trials
        self.inflationslope = ((desired_pressure) // desired_inflate_time)
        self.deflationslope = ((desired_pressure) // desired_deflate_time)
        self.start_time = time.perf_counter()
        self.elapsed_time = time.perf_counter() - self.start_time

        ### Data Logging ###
        # 2 dimensional array that stores device activity for debugging
        self.activity_log = [['Time', 'Object', 'Activity', 'Details']]
        self.stopflag = 1
        GPIO.setmode(GPIO.BCM)

        # Set channel to pin number for BOARD
        #InflateChannel = 33
        #ValveChannel = 13

        # Set channel to socket code (GPIO21) for BCM
        self.InflateChannel = 13
        self.ValveChannel = 12

        ### GPIO setup ###
        # BOARD chooses channels by printed numbers on RPi, i.e. 40
        #GPIO.setmode(GPIO.BOARD)

        # BCM chooses channels by Broadcom SOC channel, i.e. GPIO21
        # This project uses a module that sets mode for BCM. No other format is possible.
        #GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.InflateChannel, GPIO.OUT)
        GPIO.setup(self.ValveChannel, GPIO.OUT)


        ### ADC Control Functions ###
        # Guide - https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c)
        # ADS gain is not used, so it is set to the default of 1
        self.ads.gain = 1

        # ADS mode set to single stream
        self.ads.mode = ADS.Mode.CONTINUOUS
        # TODO: Offset is calculated at initialization to determine OpAmp bias
        #self.ads_offset = AnalogIn(self.ads, ADS.P0).voltage

        self.ADCoffset = self.initial_ADC_offset()


        self.Inflate = GPIO.PWM(13, 35)
        self.Deflate = GPIO.PWM(12, 10)


        ### Data Logging ###
        # 2 dimensional array that stores device activity for debugging
        self.activity_log = [['Time', 'Object', 'Activity', 'Details']]

        # Define the inflation, deflation, and valve as FlowObject state machines
        # Control pin number and object name are passed to create the state machines
        #self.inflation_pump = self.FlowObject(self.InflateChannel, 'inflation_pump')
        #self.valve = self.FlowObject(self.ValveChannel, 'valve')

    ### File Handling ###
    class FileHandler:
        # Data source indicates what generated the data being written to the file.
        # Default is set to pressure
        def __init__(self, data_source: str = "Log_") -> None:
            # File name is source + current time (YYYY-MM-DD_HH_mm_ss)
            # ex. "pressure_2023-2-19_11-32-55.csv"
            self.__file_name = data_source + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"

        def write_session(self, output) -> None:
            with open(self.__file_name, 'w') as file:
                writer = csv.writer(file)
                for row in output:
                    writer.writerow(row)

        def read_file(self):
            with open(self.__file_name, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    print('#' + str(reader.line_num) + ' ' + str(row))


    # Trigger emergency shutoff of pumps, opens valves to vent system
    def emergency_shutoff(self) -> None:
        # Input: None
        # Return: None
        self.stopflag = 0
        self.Inflate.stop()
        self.Deflate.stop()
        GPIO.cleanup()
#        self.log_activity(self.valve.set_state(False))
        self.log_activity([time.perf_counter() - self.start_time, "Emergency Shutoff"])
#        self.log_activity(self.inflation_pump.set_state(False)) # False = OFF

    def initial_ADC_offset(self) -> float:
        return AnalogIn(self.ads, ADS.P0).voltage


    def inflate_prep(self) -> None:
#        GPIO.output(12, GPIO.HIGH)
        self.Inflate.start(0)
        self.Deflate.start(100)
        self.inflatePWM = self.determine_inflate_PWM()
        self.init_inf_PWM = self.inflatePWM
        self.inflate_count = 0
        self.inf_delay = 10
        self.mod2 = -2

    def inflate_end(self) -> None:
        self.Inflate.ChangeFrequency(35)
        self.Inflate.ChangeDutyCycle(self.hold_duty)
#        self.Inflate.ChangeDutyCycle(0)

    def deflate_prep(self) -> None:
#        self.Deflate = GPIO.PWM(12, 30)
        self.Inflate.ChangeDutyCycle(0)
        self.deflate_count = 0
        self.Deflate.ChangeFrequency(50)
        self.Inflate.ChangeDutyCycle(0)
        self.deflatePWM = self.determine_deflate_PWM()
        self.init_def_PWM = self.deflatePWM
        self.def_delay = 2

    def deflate_end(self) -> None:
        self.Deflate.ChangeDutyCycle(0)


    def determine_inflate_PWM(self) -> int:
        # Determines the Duty Cycle for the PWM function
#        self.log_activity([time.perf_counter() - self.start_time, self.inflationslope, "Inflation Slope"]
        if 50 <= self.desired_pressure <=60:
            self.hold_duty = 10
        if 60 <= self.desired_pressure <=70:
            self.hold_duty = 10.5
        if 70 <= self.desired_pressure <=80:
            self.hold_duty = 11
        if 80 <= self.desired_pressure <=90:
            self.hold_duty = 11.5
        if 90 <= self.desired_pressure <=100:
            self.hold_duty = 12
        if 100 <= self.desired_pressure <=110:
            self.hold_duty = 12.5
        if 110 <= self.desired_pressure <=120:
            self.hold_duty = 13
        if 120 <= self.desired_pressure <=130:
            self.hold_duty = 13.5
        if 130 <= self.desired_pressure <=140:
            self.hold_duty = 14
        if 140 <= self.desired_pressure <=150:
            self.hold_duty = 14.5
        if 150 <= self.desired_pressure <= 160:
            self.hold_duty = 15
        elif 160 < self.desired_pressure <= 175:
            self.hold_duty = 15.8
        elif 175 < self.desired_pressure <= 185:
            self.hold_duty = 16.2
        elif 185 < self.desired_pressure <= 200:
            self.hold_duty = 16.7
        elif 200 < self.desired_pressure <= 215:
            self.hold_duty = 17.5
        elif 215 < self.desired_pressure <= 230:
            self.hold_duty = 18
        elif 230 < self.desired_pressure <= 250:
            self.hold_duty = 20

        if self.inflationslope >= 230 and self.inflationslope <= 260:
            self.inf_rate = 0.3
            return 19
        elif self.inflationslope >= 200 and self.inflationslope < 230:
            self.inf_rate = 0.27
            return 17
        elif self.inflationslope >= 150 and self.inflationslope < 200:
            self.inf_rate = 0.25
            return 16
        elif self.inflationslope >= 100 and self.inflationslope < 150:
            self.inf_rate = 0.22
            return 16
        elif self.inflationslope >= 75 and self.inflationslope < 100:
            self.inf_rate = 0.19
            return 14
        elif self.inflationslope >= 50 and self.inflationslope < 75:
            self.inf_rate = 0.18
            return 13.5
        elif self.inflationslope >= 25 and self.inflationslope < 50:
            self.inf_rate = 0.16
            return 12
        else:
            self.inf_rate = 0.14
            return 10


    def determine_deflate_PWM(self) -> int:
#        self.log_activity([time.perf_counter() - self.start_time, self.inflationslope, "Deflation Slope"])
        defstart = 97.0
        if self.deflationslope >= 200 and self.deflationslope <= 300:
            self.def_rate = 0.2
            return defstart
        elif self.deflationslope >= 150 and self.deflationslope < 200:
            self.def_rate = 0.17
            return defstart
        elif self.deflationslope >= 100 and self.deflationslope < 150:
            self.def_rate = 0.15
            return defstart
        elif self.deflationslope >= 75 and self.deflationslope < 100:
            self.def_rate = 0.14
            return defstart
        elif self.deflationslope >= 50 and self.deflationslope < 75:
            self.def_rate = 0.13
            return defstart
        elif self.deflationslope >= 25 and self.deflationslope < 50:
            self.def_rate = 0.12
            return defstart
        else:
            self.def_rate = 0.11
            return defstart


    ### Pressure Sensor Querying Function ###
    def get_pressure(self, start_offset: float) -> float:
        # Input: None
        # Return: Float (in mmHg)

        #TODO: check function call time vs variable call time
        self.elapsed_time = time.perf_counter() - self.start_time
        volt = AnalogIn(self.ads, ADS.P0).voltage
        chan = ((volt - start_offset) * 814.2485)
        # Adds current pressure, timestamp, and voltage to pressure log
        self.log_activity([self.elapsed_time, chan])
        if chan >= 300:
            self.emergency_shutoff()
        #TODO: Fine tune ads_offset to obtain correct value at start
        #return ((chan.voltage + ads_offset) * 9372)
        return chan
    # Example Output: 1.61679
    # Pressure sensor outputs 0.1067 mV per mmHg
    # Multiplier is set at 1/0.1067 * 1000, or 9372, to turn the ratio into mmHG per V because the ADC returns Volts, not mV.
    # ads_offset is an offset to counteract bias introduced by an op amp, around 4-6 mV
    # Gain for AD620 is 1 + (49,400 / Rg)
    # Rg is currently 4,700, so gain for signal is 11.51
    # 9372 / 11.51 = 814.2485, which is our gain adjusted multiplier for the ADC signal



    ### Pressure Aware Functions ###
    def raise_pressure(self, target_pressure: float) -> None:
        # Input: float
        # Return: None
        # Turn on inflation pump while current pressure below threshold
#        self.activity_log.append([time.perf_counter() - self.start_time, "Raise Pressure Active"])
        self.inflate_count += 1
        self.current_pressure = self.get_pressure(self.ADCoffset)
        #if self.inflate_count % 3 == 0:
        #    return
        #self.log_activity([time.perf_counter() - self.start_time, target_pressure - self.current_pressure, "Inflation Pressure Deviation"])
        if (self.current_pressure < target_pressure) and (self.current_pressure < self.desired_pressure) and (self.inflate_count % self.inf_delay == 0):
            mod1 = 12
            if (self.inflatePWM <= self.init_inf_PWM + mod1):
                self.inflatePWM += self.inf_rate
            else:
                self.inflatePWM = self.init_inf_PWM + mod1
            self.Inflate.ChangeDutyCycle(self.inflatePWM)
#            self.activity_log.append([time.perf_counter() - self.start_time,"Pressure",self.current_pressure, "Inflate PWM Raised", self.inflatePWM])
        elif (self.current_pressure >= target_pressure) and self.current_pressure < self.desired_pressure and (self.inflate_count % self.inf_delay == 0):
            if (self.inflatePWM >= self.init_inf_PWM - self.mod2):
                self.inflatePWM -= self.inf_rate
            else:
                self.inflatePWM = self.init_inf_PWM - self.mod2
            self.Inflate.ChangeDutyCycle(self.inflatePWM)
        elif self.current_pressure >= self.desired_pressure + 5:
            self.Inflate.ChangeDutyCycle(self.hold_duty)
#            self.activity_log.append([time.perf_counter() - self.start_time,"Pressure",self.current_pressure, "Inflate PWM Lowered", self.inflatePWM])
        else:
            return

    def lower_pressure(self, target_pressure: float) -> None:
        # Input: float
        # Return: None
        # Turn on inflation pump while current pressure below threshold
#        self.activity_log.append([time.perf_counter() - self.start_time, "Lower Pressure Start"])
        self.deflate_count += 1
        self.current_pressure = self.get_pressure(self.ADCoffset)
        if self.hold_duty > 1:
            self.hold_duty = 1
            self.Inflate.ChangeDutyCycle(self.hold_duty)

        if (self.current_pressure > target_pressure) and (self.deflate_count % self.def_delay == 0):
            if (self.deflatePWM >= self.init_def_PWM - 6):
                 self.deflatePWM -= self.def_rate
            elif self.deflatePWM < self.init_def_PWM - 6:
                self.deflatePWM = self.init_def_PWM - 6
            self.Deflate.ChangeDutyCycle(self.deflatePWM)
#            if self.hold_duty > 10:
#                self.hold_duty -= 0.1
#                self.Inflate.ChangeDutyCycle(self.hold_duty)
#            self.activity_log.append([time.perf_counter() - self.start_time,"Pressure",self.current_pressure, "Deflate PWM Lowered", self.deflatePWM])
        elif (self.current_pressure <= target_pressure) and (self.deflate_count % self.def_delay == 0):
            if (self.deflatePWM <= self.init_def_PWM + 0):
                self.deflatePWM += self.def_rate
            elif (self.deflatePWM > self.init_def_PWM + 0):
                self.deflatePWM = self.init_def_PWM + 0
            self.Deflate.ChangeDutyCycle(self.deflatePWM)
#            self.activity_log.append([time.perf_counter() - self.start_time,"Pressure",self.current_pressure, "Deflate PWM increased", self.deflatePWM])
#        self.activity_log.append([time.perf_counter() - self.start_time, "Lower Pressure End"])

    def hold_pressure(self, target_pressure: float):
        self.current_pressure = self.get_pressure(self.ADCoffset)
#        self.activity_log.append([time.perf_counter() - self.start_time, "Holding Pressure"])


    def inflation_line_pressure(self, target_pressure: float, inflate_time_elapsed: float, desired_inflate_time: float) -> float:
        ## finds slope of inflation by dividing target pressure by total inflation time, then multiplies
        ## by current time so the function can return what the pressure should be along the line
        if (desired_inflate_time < 2):
            modifier = 0.15
        else:
            modifier = 0.1
        return ((target_pressure / (desired_inflate_time - modifier)) * (inflate_time_elapsed))

    def deflation_line_pressure(self, target_pressure: float, deflate_start_time: float, desired_deflate_time: float) -> float:
        ## finds slope of deflation by dividing target pressure by total inflation time, then multiplies
        ## by current time. This value is how much the pressure should have dropped in the time elapsed, this is then
        ## subtracted from the target pressure to provide a slope downward rather than upward like inflation_line_pressure
        return (target_pressure - ((target_pressure / (desired_deflate_time - 0.1)) * (time.perf_counter() - deflate_start_time)))

    ### Input Sanitization ###
    # Ensures that user input is numeric, not alphabetic
    def input_sanitizer(self, response: str) -> float:
        # Input: String (raw user input)
        # Return: Float (numerical user input)
        if response.isnumeric():
            return float(response)
        else:
            # If response is numeric, function will continue asking recursively until an adequate number is provided
            return self.input_sanitizer(input("Please enter numbers only (Ex. 6, 400, 25.43) without any letters or special characters."))

    ### Logging Function ###
    def log_activity(self, entry: list):
        self.activity_log.append(entry)

if __name__ == "__main__":
    print("Please use the guiWindow.py file")