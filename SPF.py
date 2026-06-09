import matplotlib.pyplot as plt
import numpy as np
import CoolProp.CoolProp as CP

global Thouse
Thouse = 20
global house
house = {"height": 6, "length": 9, "width": 12}
def getQroof(Tamb):
    insulationThickness = 270#mm
    U = 40.3175/insulationThickness #Wm-2K-1
    Q = (Thouse-Tamb)*U*house['length']*house['width']
    return Q
    
def getQfloor(Tground):
    U_specific = 40.32
    thickness = 30
    U_total = U_specific/thickness
    return (Thouse-Tground)*U_total*(house['length']*house['width'])

def getQwalls(Tamb):
    Rbrick = (1/846.67)*102.5 #brick thickness of 102.5mm
    Rrockwool =  (1/40.3175)*102.5 #assume equal thickness of insulation as bricks
    Rtot = 2*Rbrick + Rrockwool
    Q = (Thouse-Tamb)*house['height']*house['length']/Rtot + (Thouse-Tamb)*house['height']*house['width']*2/Rtot
    return Q

def getQtot(Tamb,numHalfHours):
    Tground = getTground(numHalfHours)
    Qroof = getQroof(Tamb)
    Qwalls = getQwalls(Tamb)
    Qfloor = getQfloor(Tground)
    Qtot = Qroof + Qwalls + Qfloor
    return Qtot

def getTground(numHalfHours):
    x=np.arange(numHalfHours)
    Tground =  12-7*np.cos(((x+4*30*48)*2*np.pi)/(12*30*48))
    return Tground

def getTambs():
    Tambs = []
    times = []
    file = list(open('half-hourly-Tamb.csv',mode='r'))
    file = file[1:]
    for line in file:
        line = line.split(",")
        Tambs.append(float(line[1].rstrip('\n'))/10)
        times.append(line[0][-5:])

    
    return Tambs,times

def peterFunc(Tambs,times):
    Tthermostat = 17
    # Heat pump assumptions
    radiator = 60.0             # degC
    pinch_point = 5        # K
    isentropic_efficiency = 0.9
    index = np.arange(1, len(Tambs) + 1)


    # Refrigerant cycle
    Tevap = Tambs - pinch_point          # degC, refrigerant colder than ambient
    Tcond = radiator + pinch_point      # degC, refrigerant hotter than radiator water

    Pcond = CP.PropsSI('P', 'T', Tcond + 273.15, 'Q', 0, 'R134a')
    Pevap = CP.PropsSI('P', 'T', Tevap + 273.15, 'Q', 1, 'R134a')

    H1 = CP.PropsSI('H', 'T', Tevap + 273.15, 'Q', 1, 'R134a')
    S1 = CP.PropsSI('S', 'T', Tevap + 273.15, 'Q', 1, 'R134a')

    H2s = CP.PropsSI('H', 'P', Pcond, 'S', S1, 'R134a')
    H2 = H1 + (H2s - H1) / isentropic_efficiency

    H3 = CP.PropsSI('H', 'P', Pcond, 'Q', 0, 'R134a')
    H4 = H3

    q_out = H2 - H3
    w_comp = H2 - H1

    fanPower = 0.8*245 * 0 #0.8A draw at 245V
    COP = q_out / (w_comp + fanPower)

    Q_house = getQtot(Tambs,len(times))
    #heating = Q_house > 0
    heating = Tambs < Tthermostat
    heating2 = np.array([False if int(item[:2])<=6 or int(item[:2])>=22 else True for item in times])
    heating = np.array(heating) & heating2


    # compressor power needed to meet demand
   
    W_required = np.zeros_like(Q_house)
    W_required[heating] = Q_house[heating] / COP[heating]

    SPF = np.sum(Q_house[heating]) / np.sum(W_required[heating])
    print("SPF =",SPF)


    SPF_plot = np.full_like(index, SPF, dtype=float)

    COP_carnot = (Tcond + 273.15) / ((Tcond + 273.15) - (Tevap + 273.15))

    index = index/48
    Tground = getTground(len(index))
    plt.figure()
    plt.plot(index, COP, label='Cycle COP')
    plt.plot(index, SPF_plot, label=f'SPF = {SPF:.2f}')
    plt.plot(index, COP_carnot, label='Carnot COP')
    plt.plot(index,Tground,label="Ground temperature")

    print("Total work (kWhr)=",np.sum(W_required[heating])/1000*0.5)
    print("Total heat demand (kWhr)=",np.sum(Q_house[heating])/1000*0.5)


    plt.xlabel('Day')
    plt.ylabel('COP')
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.plot(index, Q_house, label='Heat Demand (W)')
    plt.plot(index, W_required, label='Compressor Power Required (W)')
    plt.xlabel('Day')
    plt.ylabel('Power (W)')
    plt.grid(True)
    plt.legend()
    plt.show()

def main():
    Tambs, times = getTambs()
    peterFunc(np.array(Tambs),np.array(times))

main()

def otherMain():
    mdot_air = 0.95 # from measurements
    qair = 1005 * 0.95
    print("q_air =",qair)

    h1 = CP.PropsSI('H','T',15+273)
    #qrefrig = h1-h4