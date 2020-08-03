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

from settings import INCHES_TO_CENIMETERS, Reading


# read_timeout is depends on port speed
# with following formula it works:
# 0.1 sec + 1.0 sec / baud rate (bits per second) * 10.0 bits (per character) * 10.0 times
# example for 115200 baud rate:
# 0.1 + 1.0 / 115200 * 10.0 * 10.0 ~ 0.1 sec
#read_timeout = 0.2 #as of June 17, this is too long
read_timeout = 0.5 #"fine-tuned" for June 19
baudRate = 115200
PRESSURE_UPPER_LIMIT = 60
INTERVAL_UPPER_LIMIT = 10

IMMEDIATE_KEY_WORD = 'IMMEDIATELY'
IMMEDIATE_INTERVAL = 3
INTERVAL_OPTIONS = [{
  'label': IMMEDIATE_KEY_WORD,
  'value': IMMEDIATE_INTERVAL
}] + [{'label': '{0} seconds'.format(i), 'value': float(i)} for i in range(1, 11)]
INTERVAL_LABELS = [i['label'] for i in INTERVAL_OPTIONS]
INTERVAL_OPTIONS_MAP = dict([(i['label'], i['value']) for i in INTERVAL_OPTIONS])
MAX_INTERVAL_VALUE = max([i['value'] for i in INTERVAL_OPTIONS])


TIMEOUT_OPTIONS = [{'label': '{0} seconds'.format(i), 'value': float(i)} for i in range(1, 11)]
TIMEOUT_LABELS = [i['label'] for i in TIMEOUT_OPTIONS]
TIMEOUT_OPTIONS_MAP = dict([(i['label'], i['value']) for i in TIMEOUT_OPTIONS])

LOOP_TIMEOUT_SECONDS = 0.5



class Gui(object):
  def __init__(self, manager, win, debug=False):
    self.manager = manager 
    self.debug = debug
    #self.lab=Label(win, text="Serial port:")
    #self.lab.place(x=30, y=20)
    #self.txtfld=Entry(win, text="Serial port")
    #self.txtfld.place(x=300, y=20)
    #self.btn_cnct=Button(win, text="Connect printer", command=self.connect)
    #self.btn_cnct.place(x=30, y=50)
    #self.btn_init=Button(win, text="Initialize", command=self.initialize, state=DISABLED)
    #self.btn_init.place(x=30, y=90)

    #self.tidal_vol=("300","400","500","750","900","1000")
    #self.lab_tv=Label(win, text='Tidal volume:')
    #self.lab_tv.place(x=30, y=180)
    #self.tv=Combobox(win, values=self.tidal_vol)
    #self.tv.place(x=240, y=180)

    #self.resp_rate=("12","16","20","32")
    #self.lab_rr=Label(win, text='Respiratory rate:')
    #self.lab_rr.place(x=30, y=210)
    #self.rr=Combobox(win, values=self.resp_rate)
    #self.rr.place(x=240, y=210)

    #self.insp_exp=("1:2")
    #self.lab_ie=Label(win, text='Inspiratory/expiratory:')
    #self.lab_ie.place(x=30, y=240)
    #self.ie=Combobox(win, values=self.insp_exp)
    #self.ie.place(x=240, y=240)

    #self.btn_run=Button(win, text="Run Ventilation", command=self.start_run,state=DISABLED)
    #self.btn_run.place(x=30, y=310)
    #self.btn_stop=Button(win, text="Stop",command=self.stop,state=DISABLED)
    #self.btn_stop.place(x=180, y=310)


    self.readings = []
    self.state = None

    self.reading_pressure = Label(win, text="Latest pressure (cmH2O)", font=("Helvetica", 18))
    self.reading_pressure.place(x=30, y=20)
    self.reading_ppeak = Label(win, text="Latest PPeak (cmH2O)", font=("Helvetica", 18))
    self.reading_ppeak.place(x=35, y=50)
    self.reading_timestamp = Label(win, text="Latest reading age (seconds)")
    self.reading_timestamp.place(x=30, y=90)
    self.reading_sample_rate = Label(win, text="Sample Rate")
    self.reading_sample_rate.place(x=30, y=110)
    self.reading_pressure_inches = Label(win, text="Latest pressure (inH2O)")
    self.reading_pressure_inches.place(x=30, y=130)
    self.exit_button = Button(win, text="Close App", command=self.exit_application)
    self.exit_button.place(x=460, y=1)

    Thread(target=self.timestampDisplayThread, args=[]).start()

    self.pressure_options = [i for i in range(0, PRESSURE_UPPER_LIMIT + 1)]
    self.max_alarm_enabled = BooleanVar(False)
    self.min_alarm_enabled = BooleanVar(False)
    self.timeout_alarm_enabled = BooleanVar(False)
    self.timeout_alarm_enabled.set(True)

    self.min_alarm_enabled_checkbox = Checkbutton(win, text="Enabled Min Pressure Alarm", variable=self.min_alarm_enabled)
    self.min_alarm_enabled_checkbox.place(x=30, y=160)
    self.min_alarm_threshold_label = Label(win, text="Minimum Pressure (cmH2O)")
    self.min_alarm_threshold_label.place(x=30, y=180)
    self.min_alarm_threshold_input = Combobox(win, values=self.pressure_options)
    self.min_alarm_threshold_input.current(0)
    self.min_alarm_threshold_input.place(x=30, y=200)
    self.min_alarm_interval_label = Label(win, text="Alarm Interval (seconds)")
    self.min_alarm_interval_label.place(x=30, y=225)
    self.min_alarm_interval_input = Combobox(win, values=INTERVAL_LABELS)
    self.min_alarm_interval_input.current(0)
    self.min_alarm_interval_input.place(x=30, y=245)

    self.max_alarm_enabled_checkbox = Checkbutton(win, text="Enabled Max Pressure Alarm", variable=self.max_alarm_enabled)
    self.max_alarm_enabled_checkbox.place(x=280, y=160)
    self.max_alarm_threshold_label = Label(win, text="Maximum Pressure (cmH2O)")
    self.max_alarm_threshold_label.place(x=280, y=180)
    self.max_alarm_threshold_input = Combobox(win, values=self.pressure_options)
    self.max_alarm_threshold_input.current(len(self.pressure_options) - 31)
    self.max_alarm_threshold_input.place(x=280, y=200)
    self.max_alarm_interval_label = Label(win, text="Alarm Interval (seconds)")
    self.max_alarm_interval_label.place(x=280, y=225)
    self.max_alarm_interval_input = Combobox(win, values=INTERVAL_LABELS)
    self.max_alarm_interval_input.current(0)
    self.max_alarm_interval_input.place(x=280, y=245)


    self.timeout_alarm_enabled_checkbox = Checkbutton(win, text="Enabled Lost Signal Alarm", variable=self.timeout_alarm_enabled)
    self.timeout_alarm_enabled_checkbox.place(x=30, y=280)
    self.timeout_alarm_interval_label = Label(win, text="Lost Signal Timeout (seconds)")
    self.timeout_alarm_interval_label.place(x=30, y=300)
    self.timeout_alarm_interval_input = Combobox(win, values=TIMEOUT_LABELS)
    self.timeout_alarm_interval_input.current(0)
    self.timeout_alarm_interval_input.place(x=30, y=320)


    self.test_alarm = Button(win, text="Test Alarm", command=self.test_alarm)
    self.test_alarm.place(x=30, y=500)
    self.clear_alarm = Button(win, text="Clear Alarm", command=self.clear_alarm)
    self.clear_alarm.place(x=30, y=530)

    self.alarm_active = False
    self.alarm_messages = []
    self.alarms_messages_var = StringVar()
    self.alarms_messages_label = Label(win, textvariable=self.alarms_messages_var, font=("Helvetica", 32))
    self.alarms_messages_label.place(x=30, y=350)
    self.alarms_messages_label['bg'] = 'lightgrey'
    self.alarms_messages_label['fg'] = 'red'
    

    self.player = None
    self.last_seek = datetime.now()
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


  def exit_application(self):
    self.manager.shutdown()

  def shutdown(self):
    self.window.destroy()

  def boot(self):
    self.window.title('3DPaV Pressure Monitor')
    self.window.geometry("529x564+0+0")
    self.window.mainloop()

  def pygletThread(self):
    self.player = Player()
    source = pyglet.resource.media('red_alert.wav')
    self.player.queue(source)
    pyglet.app.run()

  def timestampDisplayThread(self):
    while True:
      self.ui_updater_func()
      time.sleep(0.01)

  def test_alarm(self):
    self.add_alarm("Test Alarm")
  def clear_alarm(self):
    self.alarm_active = False
    self.alarm_messages = []
    self.alarms_messages_label['bg'] = 'lightgrey'
    self.window['bg'] = 'lightgrey'
  def add_alarm(self, alarm_message):
    self.alarm_active = True
    self.alarm_messages = list(set(self.alarm_messages + [alarm_message]))
    self.alarms_messages_label['bg'] = 'white'
    self.window['bg'] = 'red'
      


  def alarmThread(self):
    while True:
      now = datetime.now()
      if ((now - self.last_seek).total_seconds() > LOOP_TIMEOUT_SECONDS):
        self.player.seek(0)
        self.last_seek = now
      if (self.player):
        if (self.alarm_active):
          if not self.player.playing:
            print('START ALERT')
            self.player.play()
        else:
          if self.player.playing:
            print('STOP ALERT')
            self.player.pause()
      time.sleep(0.01)

  def updateReadings(self, state):
    self.readings.append(Reading(state['latestPressureValue'], state['timestamp']))
    self.state = state

  def ui_updater_func(self):
    state = self.state
    if state is None:
      return
    timestamp = state['timestamp']
    latestPressureValue = state['latestPressureValue']
    latestPPeakValue = state['latestPPeakValue']
    sampleRate = state['sampleRate']

    self.reading_pressure.configure(text="Latest Pressure (cmH2O): {:10.2f}".format(latestPressureValue))
    self.reading_pressure_inches.configure(text="Latest Pressure (inH2O): {:10.2f}".format(latestPressureValue / INCHES_TO_CENIMETERS))
    self.reading_ppeak.configure(text="Latest PPeak (cmH2O):    {:10.2f}".format(latestPPeakValue))
    self.reading_sample_rate.configure(text="Sample Rate (ms): {:10.2f}".format(sampleRate * 1000))
    self.alarms_messages_var.set(", \n".join(self.alarm_messages))
 
    now = datetime.now()
    min_alarm_label = self.min_alarm_interval_input.get()
    max_alarm_label = self.max_alarm_interval_input.get()
    min_alarm_interval = INTERVAL_OPTIONS_MAP[min_alarm_label]
    max_alarm_interval = INTERVAL_OPTIONS_MAP[max_alarm_label]
    self.readings = [r for r in self.readings if ((now - r.stamp).total_seconds() < (2 * MAX_INTERVAL_VALUE))]


    trigger_max_alert = False
    if (self.max_alarm_enabled.get()):
      max_samples = [r for r in self.readings if ((now - r.stamp).total_seconds() < max_alarm_interval)]
      max_threshold = int(self.max_alarm_threshold_input.get())
      if max_alarm_label == IMMEDIATE_KEY_WORD:
        trigger_max_alert = len([r for r in max_samples if r.value >= max_threshold]) > 0
      elif (len(max_samples) < len(self.readings)):
        trigger_max_alert = len([r for r in max_samples if r.value < max_threshold]) == 0

    trigger_min_alert = False
    if (self.min_alarm_enabled.get()):
      min_samples = [r for r in self.readings if ((now - r.stamp).total_seconds() < min_alarm_interval)]
      min_threshold = int(self.min_alarm_threshold_input.get())
      if min_alarm_label == IMMEDIATE_KEY_WORD:
        trigger_min_alert = len([r for r in min_samples if r.value <= min_threshold]) > 0
      elif (len(min_samples) < len(self.readings)):
        trigger_min_alert = len([r for r in min_samples if r.value > min_threshold]) == 0
        
    if trigger_min_alert:
      self.add_alarm("Min Pressure Alarm")
    if trigger_max_alert:
      self.add_alarm("Max Pressure Alarm")

    if timestamp is not None:
      delta_seconds = (datetime.now() - timestamp).total_seconds()
      self.reading_timestamp.configure(text="Latest reading: {:10.2f} seconds ago".format(delta_seconds))
      if (self.timeout_alarm_enabled.get()):
        timeout_threshold = TIMEOUT_OPTIONS_MAP[self.timeout_alarm_interval_input.get()]
        if delta_seconds > timeout_threshold:
          self.add_alarm("Signal Lost")

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
