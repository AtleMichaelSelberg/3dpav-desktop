import serial
import time
import _thread
from threading import Thread
import argparse
import threading

from tkinter import *
from tkinter.ttk import Combobox

from gcode import *

# read_timeout is depends on port speed
# with following formula it works:
# 0.1 sec + 1.0 sec / baud rate (bits per second) * 10.0 bits (per character) * 10.0 times
# example for 115200 baud rate:
# 0.1 + 1.0 / 115200 * 10.0 * 10.0 ~ 0.1 sec
#read_timeout = 0.2 #as of June 17, this is too long
read_timeout = 0.01 #"fine-tuned" for June 19
baudRate = 115200

class MyWindow(object):
  def __init__(self, win,debug=False):  
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

  @property 
  def isOk(self):
    return self._isOk

  @isOk.setter
  def isOk(self, new_value):
    if self.debug: print('isOk being updated to '+str(new_value))
    self._isOk = new_value
    if self.started_run and new_value == True: 
      if self.debug: print('adding another run thread with '+str(self.lookup))
      t = Thread(target = g_run, args =(self,self.lookup,self.debug )) 
      t.start() 
      t.join()


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
                 if self.debug: print('found DONE, breaking')
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
    if self.debug: print('BEGIN waitForDONE')
    isItOk = False
    answer = ''
    quantity = ser_printer.inWaiting()
    while True:
        if quantity > 0:
               #answer += ser_printer.read(quantity)
               answer += ser_printer.read(quantity).decode("utf-8","ignore")
               ##if 'ok' in answer.decode("utf-8", "ignore"):
               #deprecated new firmware 0622 if 'ok' in answer:
               if 'DONE' in answer:
                 if self.debug: print('found DONE, breaking')
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


#-------------------------------------------------------------------------
def main():

  parser = argparse.ArgumentParser()
  parser.add_argument('--debug',action="store_true",help='debug mode: turn on various print statements')  
  args = parser.parse_args()
  debug = False
  if args.debug: debug = True
  
  window=Tk()
  
  mywin=MyWindow(window,debug) 
  window.title('3DPaV Control')
  window.geometry("800x500+10+10")
  window.mainloop()

#-------------------------------------------------------------------------
if __name__ == "__main__":
  main()
