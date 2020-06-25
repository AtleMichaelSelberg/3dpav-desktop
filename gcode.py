import time
import threading

d_protocol_inhale={
"300mL_32BPM_1:2":"M555 F4600 Z13 Y39\n",
"400mL_12BPM_1:2":"M555 F2100 Z17 Y51\n",
"400mL_32BPM_1:2":"M555 F6200 Z17 Y51\n",
"500mL_12BPM_1:2":"M555 F2400 Z19 Y57\n",
"750mL_20BPM_1:2":"M555 F5800 Z27 Y81\n",
"900mL_16BPM_1:2":"M555 F5500 Z32 Y96\n",
"1000mL_12BPM_1:2":"M555 F4500 Z35 Y105\n",
}
d_protocol_exhale={
"300mL_32BPM_1:2":"M556 F2300 Z0 Y0\n",
"400mL_12BPM_1:2":"M556 F1050 Z0 Y0\n",
"400mL_32BPM_1:2":"M556 F3100 Z0 Y0\n",
"500mL_12BPM_1:2":"M556 F1200 Z0 Y0\n",
"750mL_20BPM_1:2":"M556 F2900 Z0 Y0\n",
"900mL_16BPM_1:2":"M556 F2750 Z0 Y0\n",
"1000mL_12BPM_1:2":"M556 F2250 Z0 Y0\n",
}

def g_init(self,debug=False):
  print("Initializing 3DPaV protocol....")
  if debug: print(";M502")
  self.printer.write(str.encode('M502\n'))
  if debug: print(";M500")
  self.printer.write(str.encode('M500\n'))
  if debug: print(";G28 Y Z")
  self.printer.write(str.encode('G28 Y Z\n'))
  if debug: print(";M400")
  self.printer.write(str.encode('M400\n'))

  time.sleep(0.5) #each command should give an immediate okay, except the M400
  self.printer.flush()
  isItOk = self.waitForOk(self.printer)
  #if 'ok' in answer.decode("utf-8", "ignore"):
  if isItOk:
    print("------ Done initializing!")
    print("")

def g_run(self,lookup,debug=False):
  self.isOk = False
  if lookup in d_protocol_inhale.keys():
    compress = d_protocol_inhale[lookup]
    decompress = d_protocol_exhale[lookup]
    if debug: print('compress: ', compress, ', decompress: ', decompress)
    self.printer.write(str.encode(compress)) 
    self.printer.write(str.encode(decompress)) 
    #self.printer.write(str.encode('M400\n'))
  else: 
    print('ERROR!!!! --------------> No ventilation protocol for this choice of settings! Try a different selection.')
    #return ''

  #if debug: print('buffer after commands:', self.printer.inWaiting())
  #self.waitForOk(self.printer)
  #do not need!!!!!
  #time.sleep(0.5) #each command should give an immediate okay, except the M400
  #self.printer.flush()
  #if debug: print('buffer after sleep/flush:', self.printer.inWaiting())
  #if debug: print('g_run, isOk: ', self.isOk)
  isItOk = self.waitForDONE(self.printer)
  if debug: print('done with thread, setting threadDone and updating self.isOk')
  self.isOk = isItOk
  

def g_stop(self,debug=False):
  print('Stopping, no extra exhale')
  #self.printer.write(str.encode(d_protocol_exhale[self.lookup])) 

