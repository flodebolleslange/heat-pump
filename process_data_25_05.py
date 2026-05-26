#!/usr/local/apps/anaconda3-5.3.1/bin/python
# Python to read in data
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import numpy as np


def plotCOPgraph(fileName,count):
    #Select how many datapoints to use

    tim, T1w, T2w, T1a, T2a, T1r, T2r, T3r, T4r, p1, p2, Ic, Qc = np.loadtxt(
        fileName,
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

    p4 = CP.PropsSI('P','T',T4r,'Q',0.5,'R134a')/100000
    delta_p = p4-p1

    #Calculate internal COP assuming no pressure drop through the condenser
    p3 = p2
    h3 = CP.PropsSI('H', 'T',T3r,'P',p3,'R134a')
    COPi = (h2-h3)/(h2-h1)

    #Calculate internal COP assuming point 3 is saturated
    h3sat = CP.PropsSI('H','T',T3r,'Q',0,'R134a')
    p3sat = CP.PropsSI('P','T',T3r,'Q',0.5,'R134a')/100000
    COPi_h3sat = (h2-h3sat)/(h2-h1)

    #Calculate the external COP
    COPe = (Qc/60000 * 1000 *4200*(T2w-T1w))/(Ic*240)

    #CALCULATE MAXIMUM VARIATION IN Q4
    #Using the first 500 datapoints:
    #h3_mean = 269146
    #h3sat_mean = 269266
    #Q4max = CP.PropsSI('Q','H',h3sat,'P',p4*100000,'R134a')
    #Q4min = CP.PropsSI('Q','H',h3,'P',p4*100000,'R134a')
    #print("Q4 Max:",np.mean(Q4max))
    #print("Q4 Min:",np.mean(Q4min)) 
    

    #plot_refridgerant_cycle( 10, np.mean(T1r), np.mean(T2r), np.mean(T3r), np.mean(T4r), np.mean(p1), np.mean(p2))

    #print("Internal COP: ",np.mean(COPi))
    #print("External COP: ",np.mean(COPe))
    #plt.plot(tim,p3,label='p3')
    #plt.plot(tim,p3sat,label='p3sat')
    '''
    plt.plot(tim,COPe,label='External COP')
    plt.plot(tim,COPi,label='Internal COP with p2=p3')
    plt.plot(tim,COPi_h3sat,label='Internal COP with h3sat')
    plt.xlabel('Time (s)')
    plt.ylabel('COP')
    plt.legend()
    plt.show()'''

    #Twrat = T2w/T1w
    pr = p2/p1
    Tvals = np.array([np.mean(T1r),np.mean(T2r),np.mean(T3r)])
    pvals = np.array([np.mean(p1),np.mean(p2),np.mean(p3)])
    svals = CP.PropsSI('S','T',Tvals,'P',pvals,'R134a')/1000
    return Tvals-273,svals,np.mean(COPe),np.mean(COPi),np.mean(pr)

def plot_satline(fluid):
    # Find critcal-point and triple-point pressures
    pc = CP.PropsSI (fluid,'pcrit')
    pt = CP.PropsSI (fluid,'ptriple')

    # Create array of pressures with geometric distribution 
    p  = np.geomspace(pt+200000,pc,500)
    # Use the CoolProp routines to get T and s (note Q is same as dryness)
    ts = CP.PropsSI ('T','P',p,'Q',0.0,fluid) - 273.15
    sf = CP.PropsSI ('S','P',p,'Q',0.0,fluid) / 1000
    sg = CP.PropsSI ('S','P',p,'Q',1.0,fluid) / 1000
    hf = CP.PropsSI ('H','P',p,'Q',0.0,fluid) / 1000
    hg = CP.PropsSI ('H','P',p,'Q',1.0,fluid) / 1000

    # Plot both wet and dry sat together (may be a bit flat)
    H = np.concatenate((hf,np.flip(hg)[1:]))
    T = np.concatenate((ts,np.flip(ts)[1:]))
    s = np.concatenate((sf,np.flip(sg)[1:]))
    p = np.concatenate((p/1e5,np.flip(p/1e5)[1:]))

    return (s, T, p, H)

def collateFullFanFiles():
    fullFanNames = ["12Lmin-1.txt","10Lmin-1.txt","9Lmin-1.txt","8Lmin-1.txt","7Lmin-1.txt"]

    for filename in fullFanNames:

        Tvals,svals,COPe,COPi,pr = plotCOPgraph("full_fan_data/"+filename,500)
        plt.scatter(svals,Tvals,label=filename.rstrip(".txt"))
        prs.append(pr)
        COPis.append(COPi)
        print(filename.rstrip(".txt"),"COPe:",COPe)

def collateFullFlowFiles():
    fullFlowNames = ["fan4.txt","fan5.txt","fan6.txt","fan7.txt","fan10.txt"]

    for filename in fullFlowNames:

        Tvals,svals,COPe,COPi,pr = plotCOPgraph("full_flow_data/"+filename,500)
        #plt.scatter(svals,Tvals,label=filename.rstrip(".txt"))
        prs.append(pr)
        COPis.append(COPi)
        print(filename.rstrip(".txt"),"COPe:",COPe)



prs = []
COPis = []
collateFullFanFiles()
s,T,p,H = plot_satline('R134a')
plt.plot(s,T)
plt.legend()
plt.xlabel("Specific Entropy (kJ/kg$^{-1}$K$^{-1}$)")
plt.ylabel("Temperature (C)")
plt.show()



plt.plot(prs,COPis,label="Full Fan data",marker='x')
labels = ["12Lmin-1","10Lmin-1","9Lmin_1","8Lmin-1","7Lmin-1"]
for i in range(5):
    plt.annotate(labels[i],xy=(prs[i],COPis[i]))
prs= []
COPis = []
collateFullFlowFiles()
plt.plot(prs,COPis,label="Full flow data",marker='x')
plt.xlabel("Refrigerant pressure ratio")
plt.ylabel("Intenal COP")

labels = ["fan4","fan5","fan6","fan7","fan10"]
for i in range(5):
    plt.annotate(labels[i],xy=(prs[i],COPis[i]),xytext=(-2,0),textcoords='offset points')
plt.legend()

plt.show()
'''
Tvals,svals = plotCOPgraph("full_flow_data/fan10.txt",500)
plt.scatter(svals,Tvals,label="fan10")

Tvals,svals = plotCOPgraph("full_flow_data/fan7.txt",500)
plt.scatter(svals,Tvals,label="fan7")

Tvals,svals = plotCOPgraph("full_flow_data/fan6.txt",500)
plt.scatter(svals,Tvals,label="fan6")

Tvals,svals = plotCOPgraph("full_flow_data/fan5.txt",500)
plt.scatter(svals,Tvals,label="fan5")

Tvals,svals = plotCOPgraph("full_flow_data/fan4.txt",500)
plt.scatter(svals,Tvals,label="fan4")

plt.plot(s,T)
plt.legend()
plt.show()'''