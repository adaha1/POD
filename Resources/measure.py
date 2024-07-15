#!/usr/bin/python2

import RPi.GPIO as GPIO
import time
import subprocess
import Adafruit_ADS1x15
import sys
import pylab
from pylab import *
import numpy as np
from matplotlib import gridspec
import os
from matplotlib.cbook import get_sample_data
from scipy.misc import imread, imresize
from matplotlib.text import OffsetFrom
import readadc

# set up buttons and GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # start inflate
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP) # quit the program
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP) # release air 
GPIO.setup(21, GPIO.OUT) # output for motor control
GPIO.setup(16, GPIO.OUT) # output for valve control

# define parameters for plot
gs = gridspec.GridSpec(5,5)
xAchse=pylab.arange(0,200,1)
yAchse=pylab.array([0]*200)
fig = pylab.figure(figsize=(13,14),facecolor='w')s
major_ticks = np.arange(0, 201, 50)
minor_ticks = np.arange(0, 201, 10)
major_ticks_y = np.arange(320, 521, 50)
minor_ticks_y = np.arange(320, 521, 10)

# subplot 1
ax = fig.add_subplot(gs[2:4,1:])
ax.set_xticks(major_ticks)
ax.set_xticks(minor_ticks, minor=True)
ax.set_yticks(major_ticks_y)
ax.set_yticks(minor_ticks_y, minor=True)
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.grid(which='both')
ax.grid(which='minor', alpha=0.2)
ax.grid(which='major', alpha=0.5)
ax.axis([0,200,320,520])
line1=ax.plot(xAchse,yAchse,'-')
manager = pylab.get_current_fig_manager()

# insert images and text into plot
im1 = imread('/home/pi/final/logo.png')
im2 = imread('/home/pi/final/black.png')
im3 = imread('/home/pi/final/heart.png')
im4 = imread('/home/pi/final/temp.png')
im5 = imread('/home/pi/final/sys.png')
im6 = imread('/home/pi/final/dia.png')
im7 = imread('/home/pi/final/cornell.jpg')

newim1 = imresize(im1, (200, 400))
newim2 = imresize(im2, (750, 950))
newim3 = imresize(im3, (50, 160))
newim4 = imresize(im4, (50, 160))
newim5 = imresize(im5, (50, 160))
newim6 = imresize(im6, (50, 160))
newim7 = imresize(im7, (90, 80))

pylab.figimage(newim2, xo=50, yo=81, origin='upper')
pylab.figimage(newim1, xo=40, yo=860, origin='upper')
pylab.figimage(newim3, xo=100, yo=750, origin='upper')
pylab.figimage(newim4, xo=100, yo=590, origin='upper')
pylab.figimage(newim5, xo=100, yo=420, origin='upper')
pylab.figimage(newim6, xo=100, yo=250, origin='upper')
pylab.figimage(newim7, xo=910, yo=960, origin='upper')

ax.text(0.85, 1.91, 'Jiayu Dong, Hongshu Ye', transform=ax.transAxes,color='black',fontsize=11)
ax.text(0.87, 1.84, 'Instructor: Joe Skovira', transform=ax.transAxes,color='black',fontsize=11) 
ax.text(0.91, 1.77, 'Cornell University', transform=ax.transAxes,color='black',fontsize=11)
ax.text(0.75, 1.70, 'Electrical & Computer Engineering', transform=ax.transAxes,color='black',fontsize=11)

# define constants and i
GAIN = 1
p_160mmHg = 11000
f=open("data.txt", "w") # specify the output file
adc = Adafruit_ADS1x15.ADS1115()
readadc.initialize()

# initialize parameters
state = 0
release = 0
num1 = 0
signal = [0] * 10000
values=[]
values = [370 for x in range(200)]
prev = 30000
count = 0
cur_data = 0
prev_data = 0
heart_count = 0
heart_rate = 0
diastolic = 0
systolic = 0
start_time = 0
d_count = 0
d = False
temp_C = 22.5

# functions
def RealtimePloter():
   CurrentXAxis=pylab.arange(len(values)-200,len(values),1)
   line1[0].set_data(CurrentXAxis,pylab.array(values[-200:]))
   ax.axis([CurrentXAxis.min(),CurrentXAxis.max(),320,520])
   manager.canvas.draw()

def process1():
   global state, release, pre_data, values, num1, signal
   global prev, count, start_time, d_count, d, temp_C
   global prev_data, cur_data,heart_count, heart_rate, diastolic, systolic
   # set up the buttons
   if (not GPIO.input(17)): # Inflate button
      state =1
      print(" ")
      print("Start inflating cuff")
   if (not GPIO.input(22)): # Exit button
      print(" ")
      sys.exit()
      print("Quit the program")
      
   # start the state machine
   if (state == 0):
      GPIO.output(21, GPIO.LOW) 
      GPIO.output(16, GPIO.LOW)
      
   elif (state == 1): 
      GPIO.output(21, GPIO.HIGH) 
      GPIO.output(16, GPIO.LOW) 
      dc = adc.read_adc(0, gain=GAIN)
      if (dc >= p_160mmHg):
         GPIO.output(21, GPIO.LOW) 
         GPIO.output(16, GPIO.LOW)
         time.sleep(1.5)
         state = 2
            
   elif (state == 2):
      # measure heart rate
      if (heart_count == 10):
         start_time = time.time()
      interval = time.time() - start_time
      if (interval > 30 and interval < 32):
         heart_rate = int((heart_count - 10) * 2.2)
     
      # read dc and ac signals
      dc = adc.read_adc(0, gain=GAIN)
      release += 1
      if (release == 80): # release air
         GPIO.output(16, GPIO.HIGH)
      elif (release == 81):
         GPIO.output(16, GPIO.LOW)
         time.sleep(1)
         release = 0
      else: # close valve
         GPIO.output(16, GPIO.LOW)
         cur_data = adc.read_adc(3, gain=GAIN)
         print cur_data
         f.write(str(cur_data) + ",")
         d_count += 1

      # compute systolic and diastolic pressure
      if (prev_data < 10000 and cur_data > 10000):
         heart_count += 1
         d_count = 0
         print "heart count" + str(heart_count)
         if (heart_count == 2):
            systolic = int((adc.read_adc(0, gain=GAIN))*0.006013+51.4762)
           
      if (heart_count > 30 and d_count >= 30 and d == False):
         d = True
         diastolic = int((adc.read_adc(0, gain=GAIN))*0.006013+51.4762)
      prev_data = cur_data
      
      if (dc < 4800):
         f.close()
         file=open("data.txt", "r")
         arr = file.read().split(',')
         index = 0
         for data in arr:
            if (data != ''):
               signal[index]= int(data)
               index += 1

         # update heart rate, blood pressure
         print heart_rate
         print 'diastolic'+ str(diastolic)
         print 'systolic'+ str(systolic)
         ax.text(-0.25, 1.15, heart_rate, transform=ax.transAxes,color='White',fontsize=32)
         ax.text(-0.25, 0.15, systolic, transform=ax.transAxes,color='White',fontsize=32)
         ax.text(-0.25, 0.65, temp_C, transform=ax.transAxes,color='White',fontsize=32)
         ax.text(-0.25, -0.35, diastolic, transform=ax.transAxes,color='White',fontsize=32)
         state = 3
         
   elif (state == 3):
      GPIO.output(16, GPIO.HIGH) # release the air
      ac = signal[num1]
      if (ac > 10000 and prev <10000):
         count += 1
      prev = ac
      if (ac > 25000):
         ac = ac / 60
      elif(ac > 15000 and ac < 25000):
         ac = ac / 50
      elif (ac < 4700 or (ac > 5200 and ac < 15000)):
         ac = 370
      else:
         ac = ac / 13
      values.append(ac)
      RealtimePloter()
      num1 += 1
      
while True:
    # read body temperature 
    sensor_data = readadc.readadc(0,
                                  readadc.PINS.SPICLK,
                                  readadc.PINS.SPIMOSI,
                                  readadc.PINS.SPIMISO,
                                  readadc.PINS.SPICS)
    millivolts = sensor_data * (3300.0 / 1024.0)
    millivolts = "%d" % millivolts
    temp_C = "%.1f" % temp_C
    temp_C = ((float(millivolts) - 100.0) / 10.0) - 33.0
    
    process1()
    pylab.show(block=False)
    time.sleep(0.05)

