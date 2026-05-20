#!/usr/local/apps/anaconda3-5.3.1/bin/python
# Python to read in data
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import numpy as np

#Select how many datapoints to use
count = 500

tim = np.empty(count)   # Initiate lists for collected data
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


data_file = open("HP_15May2026_07.txt","r",encoding='UTF-8')
title = data_file.readline() # Read first header line
props = data_file.readline() # Read second header line

#Delete header lines
data_file = [x for x in data_file if not x.startswith('#')]
# Now read in data line by line
for i in range(count):
    line = data_file[i]
    vals = line.split() # Split each line into "words"

    #Add data to lists
    tim[i] = (eval(vals[0]))
    T1w[i] = (eval(vals[1]))
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


#THIS ASSUMES THAT POINT 1 IS SATURATED
h1 = CP.PropsSI ('H' , 'T', T1r+273, 'Q', 1, 'R134a')
h2 = CP.PropsSI('H', 'T', T2r+273, 'P', 101325*p2, 'R134a')

p4 = CP.PropsSI('P','T',T4r+273,'Q',0.5,'R134a')/100000
delta_p = p4-p1

#Calculate internal COP assuming no pressure drop through the condenser
p3 = p2
h3 = CP.PropsSI('H', 'T',T3r+273,'P',101325*p3,'R134a')
COPi = (h2-h3)/(h2-h1)

#Calculate internal COP assuming point 3 is saturated
h3sat = CP.PropsSI('H','T',T3r+273,'Q',0,'R134a')
p3sat = CP.PropsSI('P','T',T3r+273,'Q',0.5,'R134a')/100000
COPi_h3sat = (h2-h3sat)/(h2-h1)

#Calculate the external COP
COPe = (Qc/60000 * 1000 *4200*(T2w-T1w))/(Ic*240)

#CALCULATE MAXIMUM VARIATION IN Q4
#Using the first 500 datapoints:
#h3_mean = 269146
#h3sat_mean = 269266
Q4max = CP.PropsSI('Q','H',h3sat,'P',p4*100000,'R134a')
Q4min = CP.PropsSI('Q','H',h3,'P',p4*100000,'R134a')
print("Q4 Max:",np.mean(Q4max))
print("Q4 Min:",np.mean(Q4min))


#plt.plot(tim,p3,label='p3')
#plt.plot(tim,p3sat,label='p3sat')
plt.plot(tim,COPe,label='External COP')
plt.plot(tim,COPi,label='Internal COP with p2=p3')
plt.plot(tim,COPi_h3sat,label='Internal COP with h3sat')
plt.xlabel('Time (s)')
plt.ylabel('COP')
plt.legend()
plt.show()



