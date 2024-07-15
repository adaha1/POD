import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesno, showerror, showinfo
import threading, time
import traceback
import os


import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from PumpControl import PumpControl
#from PumpControlTester import PumpControlTester as PumpControl

class GuiWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        ### Main window ###
        self.title('Automated Blood Pressure Occlusion')
        self.geometry('800x480')
        self.attributes("-fullscreen", True)
        self.resizable(False, False)

        # Hides the mouse
        self.config(cursor='none')
        #self.config(cursor='arrow')

        # Frames that separate functions within the main window
        self.settings_frame = ttk.Frame(self)
        self.output_frame = ttk.Frame(self)
        self.output_frame.place(relx=0.31, rely=0.01, relheight=0.97, relwidth=0.68, bordermode='ignore')


        ### State variables ###
        # This is used to allow the GUI to continue refreshing while transferring to USB 
        # or when pumps are operating, which in turn allows the GUI to interrupt pump operations
        self.running = False
        self.usb = False

        # Current trial variables that are updated during the cycle
        self.pressure = [0.0]
        self.elapsed_time = [0.0]
        #self.elapsed_time: list[float] = [0.0]

        # Shows status of trial program
        self.trial_status = tk.StringVar(value='Ready')
        self.current_pressure = tk.DoubleVar(value=0.0)
        self.current_time = tk.DoubleVar(value=0.0)

        # Current save directory
        self.directory = tk.StringVar(value='~/Desktop')

        # matplotlib objects
        self.fig, self.axis = plt.subplots(figsize=(5,3.6), dpi=80)
        self.axis.grid(color='darkgrey', alpha=0.50, linestyle='-')
        self.axis.margins(0)
        self.axis.set_xlabel("Elapsed Time", fontsize=20.0)
        self.axis.set_ylabel("Pressure (mmHg)", fontsize=20.0)
        #self.animation = FuncAnimation(self.fig, self.animate, interval=400, cache_frame_data=False)
        plt.subplots_adjust(left=0.15, bottom=0.15, right=0.99, top=0.99)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.output_frame)
        self.canvas.get_tk_widget().place(relx=0.01, rely=0.01, relheight=0.99, relwidth=0.99, bordermode='ignore')

        ### Settings Labels ###
        #label_settings = ttk.Label(self.settings_frame, text='Trial Parameters', bg='grey', font=('Arial', 16, 'bold'))
        self.Frame1 = ttk.Frame(self)
        self.Frame1.place(relx=0.01, rely=0.01, relheight=0.1, relwidth=0.30, bordermode='ignore')
        self.Frame1.configure(relief='solid')


        temps = ttk.Style(self.Frame1)
        #temps.configure('TFrame', background='white')
        temps.configure('Custom.TLabel', relief='flat')
        label_settings = ttk.Label(self, text='Trial Parameters', font=('Arial', 16, 'bold'))
        label_settings.place(relx=0.05, rely=0.02, relheight=0.085, relwidth=0.21, bordermode='ignore',)
        label_size_options = {"relheight":0.05, "relwidth":0.18, "bordermode":'ignore'}


        label_cycle = ttk.Label(self, text='Cycles: ', font=('Arial', 16, 'bold'))
        label_cycle.place(relx=0.01, rely=0.12, **label_size_options)

        label_pressure = ttk.Label(self, text='Pressure: ', font=('Arial', 16, 'bold'))
        label_pressure.place(relx=0.01, rely=0.2, **label_size_options)

        label_inflate_time = ttk.Label(self, text='Inflation: ', font=('Arial', 16, 'bold'))
        label_inflate_time.place(relx=0.01, rely=0.28, **label_size_options)

        label_hold_time = ttk.Label(self, text='Hold: ', font=('Arial', 16, 'bold'))
        label_hold_time.place(relx=0.01, rely=0.36, **label_size_options)

        label_deflate_time = ttk.Label(self, text='Deflation: ', font=('Arial', 16, 'bold'))
        label_deflate_time.place(relx=0.01, rely=0.44, **label_size_options)

        label_between_time = ttk.Label(self, text='Rest: ', font=('Arial', 16, 'bold'))
        label_between_time.place(relx=0.01, rely=0.52, **label_size_options)

        #label_start_instructions = ttk.Label(self, text="Press the START button to begin trials.\n", font=('Arial', 16, 'bold'))
        #label_start_instructions.place(relx=0.01, rely=0.60, relheight=0.05, relwidth=0.35, bordermode='ignore')

        #label_stop_instructions = ttk.Label(self, text="Press the STOP button to halt trials.\n", font=('Arial', 16, 'bold'))
        #label_stop_instructions.place(relx=0.01, rely=0.68, relheight=0.05, relwidth=0.35, bordermode='ignore')

        # drawing a vertical line

        # TODO: Customize RPI to have UDEV rule to automent
        # /etc/fstab addition to not need sudo for the copy: /dev/sda1 /mnt auto defaults,noauto,user,x-systemd.automount 0 0
        #label_choose_directory = ttk.Label(self.settings_frame, text='Choose a directory to save pressure logs.\nIf using a USB, please insert before selecting directory.')
        #label_choose_directory.grid(column=0, row=9, **options)

        ### Output Labels ###
        label_current_pressure = ttk.Label(self, text='Pressure: ', font=('Arial', 16, 'bold'))
        label_current_pressure.place(relx=0.01, rely=0.60, **label_size_options)

        label_current_pressure = ttk.Label(self, textvariable = self.current_pressure, font=('Arial', 13))
        label_current_pressure.place(relx=0.21, rely=0.60, relheight=0.05, relwidth=0.1, bordermode='ignore')

        label_current_time = ttk.Label(self, text='Run Time: ', font=('Arial', 16, 'bold'))
        label_current_time.place(relx=0.01, rely=0.68, **label_size_options)

        label_current_time = ttk.Label(self, textvariable = self.current_time, font=('Arial', 13))
        label_current_time.place(relx=0.21, rely=0.68, relheight=0.05, relwidth=0.1, bordermode='ignore')

        label_current_time = ttk.Label(self, text= str('Trial Status:'), font=('Arial', 16, 'bold'))
        label_current_time.place(relx=0.01, rely=0.76, **label_size_options)

        label_current_time_state = ttk.Label(self, text= str(self.trial_status.get()), font=('Arial', 13))
        label_current_time_state.place(relx=0.21, rely=0.76, relheight=0.05, relwidth=0.1, bordermode='ignore')

        label_current_time = ttk.Label(self, text= str('Start Trials'), font=('Arial', 16, 'bold'))
        label_current_time.place(relx=0.01, rely=0.84, **label_size_options)

        label_current_time = ttk.Label(self, text= str('Save log files to USB:'), font=('Arial', 14, 'bold'))
        label_current_time.place(relx=0.01, rely=0.92, **label_size_options)

        ### Buttons ###
        # Spin buttons allow for user input in a predetermined range

        # Number of Trials
        self.desired_number_of_trials = tk.StringVar(value='1')
        trials_spin_button = ttk.Spinbox(self,
                                            from_ = 0, to = 30,
                                            textvariable = self.desired_number_of_trials,
                                            state='readonly',
                                            width=10,
                                            font=('Arial', 14),
                                            wrap=True)
        trials_spin_button.place(relx=0.21, rely=0.13, relheight=0.05, relwidth=0.1, bordermode='ignore')



        # Set focus to first spin button on program start
        trials_spin_button.focus()

        # Desired pressure
        self.desired_pressure = tk.StringVar(value='180')
        pressure_spin_button = ttk.Spinbox(self,
                                            from_ = 150, to = 250,
                                            values = ('50','55','60','65','70','75','80','85','90','95','100','105','110','115','120','125','130','135','140','145','150', '155', '160', '165','170', '175', '180', '185', '190','195',
                                            '200', '205', '210', '215', '220','225', '230', '235', '240', '245', '250'),
                                            textvariable = self.desired_pressure,
                                            state='readonly',
                                            width=7,
                                            font=('Arial', 14),
                                            wrap=True)
        pressure_spin_button.place(relx=0.21, rely=0.21, relheight=0.05, relwidth=0.1, bordermode='ignore')

        # Desired inflate time
        self.desired_inflate_time = tk.StringVar(value='1')
        inflate_spin_button = ttk.Spinbox(self,
                                            from_ = 1, to = 20,
                                            textvariable = self.desired_inflate_time,
                                            state='readonly',
                                            width=7,
                                            font=('Arial', 14),
                                            wrap=True)
        inflate_spin_button.place(relx=0.21, rely=0.29, relheight=0.05, relwidth=0.1, bordermode='ignore')

        # Desired hold time at target pressure
        self.desired_hold_time = tk.StringVar(value='5')
        hold_spin_button = ttk.Spinbox(self,
                                            from_ = 0, to = 600,
                                            values = ('0', '1', '2', '3', '4', '5', '10', '15', '20', '25', '30', '45', '60', '90', '120', '180', '240', '300', '360', '600'),
                                            textvariable = self.desired_hold_time,
                                            state='readonly',
                                            width=7,
                                            font=('Arial', 14),
                                            wrap=True)
        hold_spin_button.place(relx=0.21, rely=0.37, relheight=0.05, relwidth=0.1, bordermode='ignore')

        # Desired deflate time
        self.desired_deflate_time = tk.StringVar(value='1')
        deflate_spin_button = ttk.Spinbox(self,
                                            from_ = 1, to = 20,
                                            textvariable = self.desired_deflate_time,
                                            state='readonly',
                                            width=7,
                                            font=('Arial', 14),
                                            wrap=True)
        deflate_spin_button.place(relx=0.21, rely=0.45, relheight=0.05, relwidth=0.1, bordermode='ignore')

        # Desired rest time between trials
        self.desired_time_between_trials = tk.StringVar(value='5')
        rest_spin_button = ttk.Spinbox(self,
                                            from_ = 0, to = 600,
                                            values = ('0', '1', '2', '3', '4', '5', '10', '15', '20', '25', '30', '45', '60', '90', '120', '180', '240', '300', '360', '600'),
                                            textvariable = self.desired_time_between_trials,
                                            state='readonly',
                                            width=7,
                                            font=('Arial', 14),
                                            wrap=True)
        rest_spin_button.place(relx=0.21, rely=0.53, relheight=0.05, relwidth=0.1, bordermode='ignore')

        # Styling for buttons
        s = ttk.Style()
        s.configure('button.TButton',
        background='#ffffff',
        #foreground='white',
        highlightthickness='20')
        s.map('button.TButton',
        foreground=[('disabled', 'grey'),
                    ('pressed', 'red'),
                    ('focus', 'green')],
        highlightcolor=[('focus', 'green'),
                        ('!focus', 'red')],
        relief=[('pressed', 'groove'),
                ('!pressed', 'ridge')])
        
        ### Buttons ###
        # Start buttons launches confirmation to start trials using
        # current configuration
        self.start_button = ttk.Button(self,
                                        text = "START",
                                        cursor='hand2',
                                        command = self.confirm,
                                        style = 'button.TButton')
        self.start_button.place(relx=0.21, rely=0.84, relheight=0.06, relwidth=0.1, bordermode='ignore')

        # Save log files to a USB
        # Prompts the user to connect a USB drive
        # Copies log files from device to USB drive
        # then deletes log files from device
        self.save_button = ttk.Button(self,
                                        text = "SAVE",
                                        command = self.save_to_usb,
                                        style = 'button.TButton')
        self.save_button.place(relx=0.21, rely=0.92, relheight=0.06, relwidth=0.1, bordermode='ignore')

        
        # Draw the graph from current Pressure readings
        self.last_graphed = self.elapsed_time[-1]
        self.print_graph(1)

    ### Actions ###
        
    # Confirmation message
    def confirm(self):
        if self.running:
            return
        self.running = True
        answer = askyesno(title = "Start trials?", message = f"""Number of trials: {self.desired_number_of_trials.get()}\nTarget pressure: {self.desired_pressure.get()}\nInflate time: {self.desired_inflate_time.get()}\nHold time: {self.desired_hold_time.get()}\nDeflate time: {self.desired_deflate_time.get()}\nReset time: {self.desired_time_between_trials.get()}\nStart trials with these settings?\n""")
        if answer:
            self.pump_control = None
            self.pump_control = PumpControl(float(self.desired_number_of_trials.get()),
                                                    float(self.desired_pressure.get()),
                                                    float(self.desired_inflate_time.get()),
                                                    float(self.desired_hold_time.get()),
                                                    float(self.desired_deflate_time.get()),
                                                    float(self.desired_time_between_trials.get()))
            self.trials = threading.Thread(target = self.start_trials)
            self.print_graph(0)            
            self.trials.start()
        else:
            self.running = False
            
    def save_to_usb(self):
        if self.running:
            return
        if askyesno(title = "Save to USB?", message = "A USB must be inserted before clicking yes. All available log files will be copied to the USB and deleted from this device. The USB will be ejected upon completion."):
            output = os.system('cp ./L* /media/admin/*/')
            if output != 0:
                if print(showerror(title = 'Something went wrong', message = 'Please disconnect and reconnect the USB and try again. If the error persists, reboot this device.')):
                    os.system('sudo eject /dev/sda')
                    time.sleep(0.3)
            else:
                os.system('rm ./L*')
                os.system('sudo eject /dev/sda')
                if showinfo(title = 'Files moved successfully', message = 'Log files were successfully copied to the USB, and deleted from this device.\n It is now safe to remove the USB'):
                    time.sleep(0.3)
        self.running = False
        return
            

    def show_status(self, pressure:float, start_time:float):
        self.pressure.append(pressure)
        self.current_pressure.set(int(pressure))
        self.elapsed_time.append(time.perf_counter() - start_time)
        self.current_time.set(int(self.elapsed_time[-1]))
        
    # Plotting
    def print_graph(self, override:int):
        if self.last_graphed + 2 > self.elapsed_time[-1] and not override:
            return
        self.last_graphed = self.elapsed_time[-1]
        self.axis.clear()
        self.axis.grid(color='darkgrey', alpha=0.50, linestyle='-')
        self.axis.margins(0)
        self.axis.set_xlabel("Elapsed Time")
        self.axis.set_ylabel("Pressure (mmHg)")
        self.axis.plot(self.elapsed_time, self.pressure, label = 'Current Pressure')
        self.axis.legend(loc=0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.output_frame)
        self.canvas.get_tk_widget().place(relx=0.01, rely=0.01, relheight=0.99, relwidth=0.99, bordermode='ignore')

    def stop_trials(self):
        self.running = False

    def start_trials(self):
        # Set running marker to True
        self.running = True
        PC = self.pump_control

        ## Total trial time equation. 
        total_trial_time = PC.desired_number_of_trials * (PC.desired_inflate_time + PC.desired_hold_time + PC.desired_deflate_time) + (PC.desired_time_between_trials * (PC.desired_number_of_trials - 1))
        self.pressure, self.elapsed_time = [0.0], [0.0]
        self.last_graphed = self.elapsed_time[-1]
        
        start_time = time.perf_counter()

        try:
            cycle_number = 1
            self.trial_status.set('Running Trials...')
            ADCoffset = PC.initial_ADC_offset()
            while self.running and (time.perf_counter() - start_time) < total_trial_time and PC.stopflag:            
                ## INFLATION CYCLE.
                ## Starting time for inflation is recorded, and a function is called to compare current pressure
                ## to desired pressure at the current time. While loop keeps this running for as long as desired inflate time
                ## has not been reached
                PC.log_activity([PC.elapsed_time, "Raise Pressure Start", PC.get_pressure(ADCoffset)])
                PC.inflate_prep()
                inflate_start_time = time.perf_counter()

                while PC.stopflag and self.running and ((time.perf_counter() - PC.desired_inflate_time - inflate_start_time) <= 0):
                    PC.raise_pressure(PC.inflation_line_pressure(PC.desired_pressure, (time.perf_counter() - inflate_start_time), PC.desired_inflate_time))
                    self.show_status(PC.get_pressure(ADCoffset), start_time)
#                    self.print_graph(0)
                
                PC.log_activity([PC.elapsed_time, "Actual inflate time", str(time.perf_counter() - inflate_start_time)])
                self.show_status(PC.get_pressure(ADCoffset), start_time)

                ## HOLD CYCLE
                ## While loop essentially waits the program for the hold time requested            
                hold_start_time = time.perf_counter()
                PC.inflate_end()
                while PC.stopflag and self.running and ((time.perf_counter() - hold_start_time) <= PC.desired_hold_time):
                    PC.hold_pressure(PC.desired_pressure)
                    self.show_status(PC.get_pressure(ADCoffset), start_time)
#                    self.print_graph(0)

                PC.log_activity([PC.elapsed_time, "Actual hold time", str(time.perf_counter() - hold_start_time)])
                self.show_status(PC.get_pressure(ADCoffset), start_time)

                ## DEFLATION CYCLE
                ## Starting time for deflation is recorded, and a function is called to compare current pressure
                ## to desired pressure at the current time. While loop keeps this running for as long as desired deflation time
                ## has not been reached          
                PC.deflate_prep()
                PC.log_activity([PC.elapsed_time, "Lower Pressure Start", PC.get_pressure(ADCoffset)])
                deflate_start_time = time.perf_counter()
                while PC.stopflag and self.running and ((time.perf_counter() - PC.desired_deflate_time - deflate_start_time) <= 0):
                    PC.lower_pressure(PC.deflation_line_pressure(PC.desired_pressure, deflate_start_time, PC.desired_deflate_time))
                    self.show_status(PC.get_pressure(ADCoffset), start_time)
#                    self.print_graph(0)
                
                PC.log_activity([PC.elapsed_time, "Actual deflate time", str(time.perf_counter() - deflate_start_time)])
                self.show_status(PC.get_pressure(ADCoffset), start_time)
                PC.deflate_end()
                rest_start_time = time.perf_counter()
                while PC.stopflag and self.running and (((time.perf_counter() - rest_start_time) <= PC.desired_time_between_trials)) and cycle_number < int(PC.desired_number_of_trials):
                    self.show_status(PC.get_pressure(ADCoffset), start_time)
                    
#                    self.print_graph(0)
                cycle_number += 1
                self.print_graph(1)
        except:
            PC.emergency_shutoff()
            self.trial_status.set("ERROR")
            PC.log_activity([time.perf_counter() - PC.start_time, traceback.format_exc()])
        PC.emergency_shutoff()
        log_file = PC.FileHandler()
        log_file.write_session(PC.activity_log)
        

        if self.running:
            self.trial_status.set('COMPLETE')
            self.running = False
            self.print_graph(0)
        else:
            self.trial_status.set('HALTED')


# Initialize main window
root_window = GuiWindow()

root_window.bind_all('y', lambda event: root_window.stop_trials())

if __name__ == '__main__':
    root_window.mainloop()
