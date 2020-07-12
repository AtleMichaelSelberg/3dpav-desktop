import serial
import time
import _thread
from threading import Thread
import argparse
import threading
from datetime import datetime

import pyglet
from pyglet.media import Player, load

from tkinter import *
from tkinter.ttk import Combobox

from gcode import *

# read_timeout is depends on port speed
# with following formula it works:
# 0.1 sec + 1.0 sec / baud rate (bits per second) * 10.0 bits (per character) * 10.0 times
# example for 115200 baud rate:
# 0.1 + 1.0 / 115200 * 10.0 * 10.0 ~ 0.1 sec
#read_timeout = 0.2 #as of June 17, this is too long
read_timeout = 0.5 #"fine-tuned" for June 19
baudRate = 115200



class Gui(object):
  def __init__(self, manager, win, debug=False):
    self.manager = manager 
    self.debug = debug
    self.lab=Label(win, text="Serial port:")
    self.lab.place(x=60, y=20)
    self.txtfld=Entry(win, text="Serial port")
    self.txtfld.place(x=150, y=20)
    self.btn_cnct=Button(win, text="Connect printer", command=self.connect)
    self.btn_cnct.place(x=60, y=50)
    self.btn_init=Button(win, text="Initialize", command=self.initialize, state=DISABLED)
    self.btn_init.place(x=60, y=90)

    self.tidal_vol=("300","400","500","750","900","1000")
    self.lab_tv=Label(win, text='Tidal volume:')
    self.lab_tv.place(x=60, y=180)
    self.tv=Combobox(win, values=self.tidal_vol)
    self.tv.place(x=240, y=180)

    self.resp_rate=("12","16","20","32")
    self.lab_rr=Label(win, text='Respiratory rate:')
    self.lab_rr.place(x=60, y=210)
    self.rr=Combobox(win, values=self.resp_rate)
    self.rr.place(x=240, y=210)

    self.insp_exp=("1:2")
    self.lab_ie=Label(win, text='Inspiratory/expiratory:')
    self.lab_ie.place(x=60, y=240)
    self.ie=Combobox(win, values=self.insp_exp)
    self.ie.place(x=240, y=240)

    self.btn_run=Button(win, text="Run Ventilation", command=self.start_run,state=DISABLED)
    self.btn_run.place(x=60, y=310)
    self.btn_stop=Button(win, text="Stop",command=self.stop,state=DISABLED)
    self.btn_stop.place(x=180, y=310)





    self.reading_timestamp = Label(win, text="Latest reading")
    self.reading_timestamp.place(x=480, y=20)
    self.reading_pressure = Label(win, text="Latest pressure")
    self.reading_pressure.place(x=480, y=40)
    self.reading_ppeak = Label(win, text="Latest PPeak")
    self.reading_ppeak.place(x=480, y=60)
    self.reading_sample_rate = Label(win, text="Sample Rate")
    self.reading_sample_rate.place(x=480, y=80)
    self.reading_timestamp_value = None
    Thread(target=self.timestampDisplayThread, args=[]).start()

   
    self.min_alarm_value_var = StringVar()
    self.min_alarm_value_var.set("0")
    self.min_alarm_value_var.trace("w", self.min_alarm_value_validate)
    self.min_alarm_value = 0
    self.min_alarm_enabled = BooleanVar(False)
    self.max_alarm_value_var = StringVar()
    self.max_alarm_value_var.set("50")
    self.max_alarm_value_var.trace("w", self.max_alarm_value_validate)
    self.max_alarm_value = 50
    self.max_alarm_enabled = BooleanVar(False)
    
    self.min_alarm_enabled_checkbox = Checkbutton(win, text="Enabled Min Pressure Alarm", variable=self.min_alarm_enabled)
    self.min_alarm_enabled_checkbox.place(x=480, y=120)
    self.min_alarm_value_input = Entry(win, textvariable=self.min_alarm_value_var)
    self.min_alarm_value_input.place(x=480, y=140)

    self.max_alarm_enabled_checkbox = Checkbutton(win, text="Enabled Max Pressure Alarm", variable=self.max_alarm_enabled)
    self.max_alarm_enabled_checkbox.place(x=480, y=160)
    self.max_alarm_value_input = Entry(win, textvariable=self.max_alarm_value_var)
    self.max_alarm_value_input.place(x=480, y=180)

    self.trigger_max_alert = False
    self.trigger_min_alert = False

    self.player = None
    Thread(target=self.pygletThread, args=[]).start()
    Thread(target=self.alarmThread, args=[]).start()


    #TODO
    #self.place_dropdown(win,'Tidal volume:', self.tidal_vol, 60, 180) 
    #self.place_dropdown(win,'Respiratory rate:', self.resp_rate, 60, 210) 
    #self.place_dropdown(win,'Inspiratory/expiratory:', self.insp_exp, 60, 240) 
    #self.place_btn(win,"Run ventilation", self.run,60,290)
    #self.place_btn(win,"Stop", self.run,180,290)

    #3dpav control
    self.printer = None
    self.lookup = None
    self.started_run = False
    self._isOk = False

    self.window = win

  def boot(self):
    self.window.title('3DPaV Control')
    self.window.geometry("800x500+10+10")
    self.window.mainloop()

  def pygletThread(self):
    self.player = Player()
    source = pyglet.resource.media('red_alert.wav')#load('./red_alert.mp3')
    self.player.queue(source)
    self.player.loop = True
    window = pyglet.window.Window()
    pyglet.app.run()

  def timestampDisplayThread(self):
    while True:
      self.updateTimestampDisplay()
      time.sleep(0.1)

  def min_alarm_value_validate(self, *args):
    raw_min_value = re.match("(^-?[0-9]+)", self.min_alarm_value_var.get()) 
    if (raw_min_value):
      self.min_alarm_value = int(raw_min_value.group(0))
    str_min_value = str(self.min_alarm_value)
    if (str_min_value != self.min_alarm_value_var.get()):
      self.min_alarm_value_var.set(str_min_value)
    return True

  def max_alarm_value_validate(self, *args):
    raw_max_value = re.match("(^-?[0-9]+)", self.max_alarm_value_var.get()) 
    if (raw_max_value):
      self.max_alarm_value = int(raw_max_value.group(0))
    str_max_value = str(self.max_alarm_value)
    if (str_max_value != self.max_alarm_value_var.get()):
      self.max_alarm_value_var.set(str_max_value)
    return True


  def alarmThread(self):
    while True:
      if (self.player):
        if (self.trigger_max_alert or self.trigger_min_alert):
          if not self.player.playing:
            print('START ALERT')
            self.player.play()
        else:
          if self.player.playing:
            print('STOP ALERT')
            self.player.pause()
      time.sleep(0.1)

  def updateReadings(self, timestamp, latestPressureValue, latestPPeakValue, sampleRate):
    self.reading_timestamp_value = timestamp
    self.reading_pressure.configure(text="Latest pressure: {:10.2f}".format(latestPressureValue))
    self.reading_ppeak.configure(text="Latest PPeak: {:10.2f}".format(latestPPeakValue))
    self.reading_sample_rate.configure(text="Sample rate (ms): {:10.2f}".format(sampleRate * 1000))

    self.trigger_max_alert = self.max_alarm_enabled.get() and (latestPressureValue >= self.max_alarm_value)
    self.trigger_min_alert = self.min_alarm_enabled.get() and (latestPressureValue <= self.min_alarm_value)

    self.updateTimestampDisplay()

  def updateTimestampDisplay(self):
    if self.reading_timestamp_value is not None:
      delta_seconds = (datetime.now() - self.reading_timestamp_value).total_seconds()
      self.reading_timestamp.configure(text="Latest reading: {:10.2f} seconds ago".format(delta_seconds))

  @property 
  def isOk(self):
    return self._isOk

  @isOk.setter
  def isOk(self, new_value):
    if self.debug: print('isOk being updated to '+str(new_value))
    self._isOk = new_value
    if self.started_run and new_value == True: 
      if self.debug: print('adding another run with '+str(self.lookup))
      g_run(self,self.lookup,self.debug)
      #deprecated? keep it all on one thread for now 
      #t = Thread(target = g_run, args =(self,self.lookup,self.debug )) 


  #------------------------- aesthetics
  def place_dropdown(self, win, txt, vals, xstart=60, ystart=180):
    self.lab=Label(win, text=txt)
    self.lab.place(x=xstart, y=ystart)
    self.box=Combobox(win, values=vals)
    self.box.place(x=xstart+160, y=ystart)
  def place_btn(self, win, txt,cmd, xstart=60, ystart=180):
    self.btn=Button(win, text=txt,command=cmd)
    self.btn.place(x=xstart, y=ystart)

    

  #-------------------------- ventilator methods
  def connect(self):
    if self.txtfld.get() == '': path = '/Users/juliagonski/Documents/Columbia/3DprinterAsVentilator/pronsoleWork/Printator/sim'
    else: path = self.txtfld.get()
    ser_printer = serial.Serial(path, baudRate)

    print("Connecting to printer...")
    time.sleep(1)  # Allow time for response
    if self.debug: print("Connection response from printer:", ser_printer.read(ser_printer.inWaiting()))
    #ser_printer.write(str.encode('M400\n'))
    #ser_printer.write(str.encode('M400\n'))
    answer = ser_printer.readline()

    if 'ok' in answer.decode("utf-8", "ignore"):
      print("------ Done connecting!")
      print("")
    self.printer=ser_printer
    self.btn_init["state"] = "normal"
    
  def initialize(self):
    g_init(self,self.debug)
    self.btn_run["state"] = "normal"

  #def check_run(self, win):
  #  if self.started_run == 1:
  #    answer = self.waitForOk(self.printer)
  #    if self.debug: print("waiting response from printer?", answer)
  #    if 'ok' in answer.decode("utf-8", "ignore"): g_run(self,self.debug)
  #    #else: print('not ventilating, not adding more runs')
  #  win.after(2000,self.check_run,win)

  def start_run(self):
    self.printer.flush()
    self.started_run = True
    sel_tv=self.tv.get()
    sel_rr=self.rr.get()
    sel_ie=self.ie.get()
    self.lookup = sel_tv+"mL_"+sel_rr+"BPM_"+sel_ie
    print('Started new protocol: '+str(self.lookup))
    self.btn_stop["state"] = "normal"
    #Start first thread, join subsequent ones 
    t_orig = Thread(target = g_run, args =(self,self.lookup,self.debug )) 
    t_orig.start() 

  def stop(self):
    self.started_run = False
    self.printer.flush()
    g_stop(self,self.debug)

  def waitForOk(self, ser_printer):
    if self.debug: print('BEGIN waitForOk')
    isItOk = False
    answer = ''
    quantity = ser_printer.inWaiting()
    while True:
        if quantity > 0:
               #answer += ser_printer.read(quantity)
               answer += ser_printer.read(quantity).decode("utf-8","ignore")
               ##if 'ok' in answer.decode("utf-8", "ignore"):
               if 'ok' in answer:
                 if self.debug: print('found ok, breaking')
                 isItOk = True
                 break
        else:
               time.sleep(read_timeout)  
        quantity = ser_printer.inWaiting()
        #if quantity == 0:
               #if self.debug: print('-------> No lines to read out')
               #print('ERROR connecting!!!')
               #raise ImportError()
               #break
    if self.debug: print('resulting answer: ', answer)
    return isItOk

  def waitForDONE(self, ser_printer):
    if self.debug: print('----- BEGIN waitForDONE')
    isItOk = False
    answer = ''
    quantity = ser_printer.inWaiting()
    while True:
        if quantity > 0:
               if self.debug: print('----- reading what the printer has to say: ', ser_printer.read(quantity).decode("utf-8","ignore"))
               answer += ser_printer.read(quantity).decode("utf-8","ignore")
               #deprecated new firmware 0622 if 'ok' in answer:
               if 'DECOMPRESSDONE' in answer:
                 if self.debug: print('----- found DECMOMPRESSDONE in answer')
                 isItOk = True
                 break
        else:
               time.sleep(read_timeout)  
        quantity = ser_printer.inWaiting()
        #if quantity == 0:
               #if self.debug: print('-------> No lines to read out')
               #print('ERROR connecting!!!')
               #raise ImportError()
               #break
    if self.debug: print('----- resulting answer of concatented printer output (should end in DECOMPRESSDONE): ', answer)
    return isItOk


#-------------------------------------------------------------------------
def main():

  parser = argparse.ArgumentParser()
  parser.add_argument('--debug',action="store_true",help='debug mode: turn on various print statements')  
  args = parser.parse_args()
  debug = False
  if args.debug: debug = True
  
  window=Tk()
  
  mywin=Gui(None, window, debug) 


#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
