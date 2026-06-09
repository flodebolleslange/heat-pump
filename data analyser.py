#!/usr/local/apps/anaconda3-5.3.1/bin/python
# Python to read in data
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import numpy as np
from ts_plotter import plot_refridgerant_cycle

#Select how many datapoints to use
count = 1000

tim, T1w, T2w, T1a, T2a, T1r, T2r, T3r, T4r, p1, p2, Ic, Qc = np.loadtxt(
    r"full_flow_data\fan10.txt",
    comments='#',
    skiprows=2,
    unpack=True,
)

tim = np.array(tim[:count])   # Only read in the number of datapoints specified
T1w = np.array(T1w[:count]) + 273.15
T2w = np.array(T2w[:count]) + 273.15
T1a = np.array(T1a[:count]) + 273.15
T2a = np.array(T2a[:count]) + 273.15  
T1r = np.array(T1r[:count]) + 273.15
T2r = np.array(T2r[:count]) + 273.15
T3r = np.array(T3r[:count]) + 273.15 
T4r = np.array(T4r[:count]) + 273.15
p2 = np.array(p2[:count]) * 100000  # Convert from bar to Pa
p1 = np.array(p1[:count]) * 100000
Ic = np.array(Ic[:count])
Qc = np.array(Qc[:count])

#print(tim)
#THIS ASSUMES THAT POINT 1 IS SATURATED
h1 = CP.PropsSI ('H' , 'T', T1r, 'Q', 1, 'R134a')
h2 = CP.PropsSI('H', 'T', T2r, 'P', p2, 'R134a')

#Calculate internal COP assuming no pressure drop through the condenser
p3 = p2
h3 = CP.PropsSI('H', 'T',T3r,'P',p3,'R134a')
COPi = (h2-h3)/(h2-h1)

#Calculate internal COP assuming point 3 is saturated
h3sat = CP.PropsSI('H','T',T3r,'Q',0,'R134a')
p3sat = CP.PropsSI('P','T',T3r,'Q',0,'R134a')/100000
COPi_h3sat = (h2-h3sat)/(h2-h1)

#Calculate the external COP
COPe = (Qc/60000 * 1000 *4200*(T2w-T1w))/(Ic*240)

h4 = h3
# use Q=0.5 since we know 4 is in the saturation dome
p4 = CP.PropsSI('P','Q',0.5,'T',T4r,'R134a')
delta_p = p4-p1

mdotrefrig = 0.95*1005*(T1a-T2a)/(h1-h4)
comp_work_ideal = mdotrefrig * (h2-h1)
comp_work_real = (Ic-0.8) * 240
comp_effic = comp_work_ideal/comp_work_real
plt.scatter(p1/100000,comp_effic)
plt.ylabel('compressor isentropic efficiency')
plt.xlabel('$P_1$ (bar)')
plt.show()

#CALCULATE MAXIMUM VARIATION IN Q4
#Using the first 500 datapoints:
#h3_mean = 269146
#h3sat_mean = 269266
Q4max = CP.PropsSI('Q','H',h3sat,'P',p4*100000,'R134a')
Q4min = CP.PropsSI('Q','H',h3,'P',p4*100000,'R134a')
print("Q4 Max:",np.mean(Q4max))
print("Q4 Min:",np.mean(Q4min)) 

# plot_refridgerant_cycle(tim[-100], T1r[-100], T2r[-100], T3r[-100], T4r[-100], p1[-100], p2[-100])


#plt.plot(tim,p3,label='p3')
#plt.plot(tim,p3sat,label='p3sat')
# plt.plot(tim,COPe,label='External COP')
# plt.plot(tim,COPi,label='Internal COP with p2=p3')
# plt.plot(tim,COPi_h3sat,label='Internal COP with h3sat')
# plt.xlabel('Time (s)')
# plt.ylabel('COP')
# plt.legend()
# plt.show()



