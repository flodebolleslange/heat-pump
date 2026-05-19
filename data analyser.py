#!/usr/local/apps/anaconda3-5.3.1/bin/python
# Python to read in data
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import numpy as np

count = 100
tim = np.empty(count)   # Initiate lists for time and inlet water temperature
T1w = np.empty(count)
T2w =np.empty(count)
T1a = np.empty(count)
T2a = np.empty(count)
T1r = np.empty(count)
T2r = np.empty(count)
T3r = np.empty(count)
T4r = np.empty(count)
p2 = np.empty(count)
p1 = np.empty(count)
Ic = np.empty(count)
Qc = np.empty(count)


#file_name = input('HP_15May2026_07.txt') # Prompt for file name and open fil
data_file = open(r"C:\Users\Alexa\OneDrive\Documents\Alexander\Year 3\Heat pump\HP_15May2026_07.txt","r")

title = data_file.readline() # Read first header line
props = data_file.readline() # Read second header line

data_file = [x for x in data_file if not x.startswith('#')]
# Now read in data line by line
for i in range(count):
    line = data_file[i]
    vals = line.split() # Split each line into "words"
    tim[i] = (eval(vals[0])) # Convert words (strings) to floating point
    T1w[i] = (eval(vals[1])) # and append to arrays tim[] and T1w
    T2w[i] = (eval(vals[2]))
    T1a[i] = (eval(vals[3]))
    T2a[i] = (eval(vals[4]))
    T1r[i] = (eval(vals[5]))
    T2r[i] = (eval(vals[6]))
    T3r[i] = (eval(vals[7]))
    T4r[i] = (eval(vals[8]))
    p2[i] = (eval(vals[10]))
    Ic[i] = (eval(vals[11]))
    Qc[i] = (eval(vals[12]))




   
    #print(count)



h1 = CP.PropsSI ('H' , 'T', T1r+273, 'Q', 1, 'R134a')
h2 = CP.PropsSI('H', 'T', T2r+273, 'P', 101325*p2, 'R134a')
h3sat = CP.PropsSI('H','T',T3r+273,'Q',0,'R134a')

p4 = CP.PropsSI('P','T',T4r+273,'Q',0.5,'R134a')/100000
delta_p = p4-p1
p3 = p2

p3sat = CP.PropsSI('P','T',T3r+273,'Q',0.5,'R134a')/100000
#h3 = CP.PropsSI('H', 'T',T3r+273,'P',p3,'R134a')
#COPi = np.array((h2-h3)/(h2-h1))
COPe = (Qc/60000 * 1000 *4200*(T2w-T1w))/(Ic*240)


#plt.plot(tim,p3,label='p3')
#plt.plot(tim,p3sat,label='p3sat')
plt.plot(tim,COPe)
plt.legend()
plt.show()



