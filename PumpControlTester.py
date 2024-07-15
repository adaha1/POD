#!/usr/bin/python3.9.6
import time
from datetime import datetime
import csv

class PumpControlTester:
    def __init__(self, 
                desired_number_of_trials: float,
                desired_pressure: float,
                desired_inflate_time: float,
                desired_hold_time: float,
                desired_deflate_time: float,
                desired_time_between_trials: float):
        
        ### Trial Settings ###
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

        ### Test Variables ###
        # Only used for program debugging
        self.current_pressure = 0.0

        ### Data Logging ###
        # 2 dimensional array that stores device activity for debugging
        self.activity_log = [['Time', 
                              'Object', 
                              'Activity', 
                              'Details']]
        self.stopflag = 1
        
        # Define the inflation, deflation, and valve as FlowObject state machines
        # Control pin number and object name are passed to create the state machines
        self.inflation_pump = self.FlowObject('inflation_pump')
        self.deflation_pump = self.FlowObject('deflation_pump')
        self.valve = self.FlowObject('valve')

    ### File Handling ###
    class FileHandler:
        # Data source indicates what generated the data being written to file.
        # Default is set to pressure
        def __init__(self, data_source: str = "Log_") -> None:
            # File name is source + current time (YYYY-MM-DD_HH_mm_ss)
            # ex. "pressure_2023-2-19_11-32-55.csv"
            self.__file_name = data_source \
                            + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") \
                            + ".csv"
        
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
        def __init__(self, name: str) -> None:
            # Input: int (Pin number), str (name of FlowObject)
            # Return: None
            self.__state = False # False = OFF/OPEN, True = ON/CLOSED
            self.__name = name

        # Set the desired state of the pump or valve
        def set_state(self, state: bool) -> list:
            # Input: boolean (flow state)
            # Return: None
            self.__state = state
            return self.set_action()

        # Get the current state of the pump or valve
        def get_state(self) -> bool:
            # Input: None
            # Return: boolean (current flow state)
            return self.__state

        # Apply the current state to the pump or valve
        def set_action(self) -> list:
            # Input: None
            # Return: None
            if not self.__state:
                return [datetime.now().strftime("%H:%M:%S"), "Turn off " + self.__name]
            else:
                return [datetime.now().strftime("%H:%M:%S"), "Turn on " + self.__name]

    # Trigger emergency shutoff of pumps, opens valves to vent system
    def emergency_shutoff(self) -> None:
        # Input: None
        # Return: None
        self.log_activity([time.perf_counter() - self.start_time, 
                           "Emergency Shutoff"])
        self.log_activity(self.inflation_pump.set_state(False)) # False = OFF
        self.log_activity(self.deflation_pump.set_state(False))
        self.log_activity(self.valve.set_state(False))

    def raise_pressure(self, target_pressure: float) -> None:
        # Input: float 
        # Return: None
        # Turn on inflation pump while current pressure below threshold
        self.log_activity([time.perf_counter() - self.start_time, 
                           "Raise Pressure Start"])

        self.current_pressure = target_pressure

        #print(self.get_pressure(0.00))
        self.log_activity([time.perf_counter() - self.start_time, 
                           "Raise Pressure End"])

    def lower_pressure(self, target_pressure: float) -> None:
        # Input: float 
        # Return: None
        # Turn on inflation pump while current pressure below threshold
        self.log_activity([time.perf_counter() - self.start_time, 
                           "Lower Pressure Start"])
        self.current_pressure = target_pressure

        self.log_activity([time.perf_counter() - self.start_time, "Lower Pressure End"])

    def inflation_line_pressure(self, target_pressure: float, 
                                inflate_time_elapsed: float, 
                                desired_inflate_time: float) -> float:
        ## finds slope of inflation by dividing target pressure by total inflation time, 
        ## then multiplies by current time so the function can return 
        ## what the pressure should be along the line
        return ((target_pressure // desired_inflate_time) * inflate_time_elapsed)

    def deflation_line_pressure(self, target_pressure: float, 
                                deflate_start_time: float, 
                                desired_deflate_time: float) -> float:
        ## finds slope of deflation by dividing target pressure by total inflation time, 
        ## then multipliesby current time. This value is
        ## how much the pressure should have dropped in the time elapsed,
        ## this is then subtracted from the target pressure to provide 
        ## a slope downward rather than upward like inflation_line_pressure
        return (target_pressure 
                - ((target_pressure // desired_deflate_time) 
                   * (time.perf_counter() - deflate_start_time)))
    
    ### Pressure Sensor Querying Function ###
    def get_pressure(self, offset: float) -> float:
        # Input: None
        # Return: Float (in mmHg)
        
        #TODO: check function call time vs variable call time
        self.elapsed_time = time.perf_counter() - self.start_time

        # Adds current pressure, timestamp, and voltage to pressure log
        self.log_activity([self.elapsed_time, 
                           self.current_pressure])

        return self.current_pressure
    
    ### Logging Function ###
    def log_activity(self, entry: list):
        self.activity_log.append(entry)


        
    def initial_ADC_offset(self) -> float:
        return 0.00
        
        
    def inflate_prep(self) -> None:
        #self.Deflate.start(100)
        #self.Inflate.start(0)
        #self.inflatePWM = self.determine_inflate_PWM()
        #self.init_inf_PWM = self.inflatePWM
        pass
        
    def inflate_end(self) -> None:
        #self.Inflate.ChangeDutyCycle(0)
        pass
        
    def deflate_prep(self) -> None:
        #self.deflatePWM = self.determine_deflate_PWM()
        #self.init_def_PWM = self.deflatePWM
        pass
        
    def deflate_end(self) -> None:
        #self.Deflate.ChangeDutyCycle(0)
        #self.valve.set_state(False)
        pass