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
    return (Thouse-Tground)*U_total/(house['length']*house['width'])

def getQwalls(Tamb):
    Rbrick = (1/846.67)*102.5 #brick thickness of 102.5mm
    Rrockwool =  (1/40.3175)*102.5 #assume equal thickness of insulation as bricks
    Rtot = 2*Rbrick + Rrockwool
    Q = (Thouse-Tamb)*house['height']*house['length']/Rtot + (Thouse-Tamb)*house['height']*house['width']*2/Rtot
    return Q

def getQtot(Tamb):
    Qroof = getQroof(Tamb)
    Qwalls = getQwalls(Tamb)
    Qfloor = getQfloor(15)
    Qtot = Qroof + Qwalls + Qfloor
    return Qtot


def getTambs():
    Tambs = []
    times = []
    file = list(open('weather-raw.csv',mode='r'))
    file = file[1:]
    for line in file:
        line = line.split(",")
        Tambs.append(float(line[1].rstrip('\n'))/10)
        times.append(line[0][-5:])

    #print(times)
    
    return Tambs

def peterFunc(Tambs):
    # Heat pump assumptions
    radiator = 60.0             # degC
    pinch_point = 5        # K
    isentropic_efficiency = 0.9
    days = np.arange(1, len(Tambs) + 1)


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

    COP = q_out / w_comp

    Q_house = getQtot(Tambs)
    heating = Q_house > 0


    # compressor power needed to meet demand
    W_required = np.zeros_like(Q_house)
    W_required[heating] = Q_house[heating] / COP[heating]

    SPF = np.sum(Q_house[heating]) / np.sum(W_required[heating])
    print("SPF =",SPF)


    SPF_plot = np.full_like(days, SPF, dtype=float)

    COP_carnot = (Tcond + 273.15) / ((Tcond + 273.15) - (Tevap + 273.15))

    plt.figure()
    plt.plot(days, COP, label='Cycle COP')
    plt.plot(days, SPF_plot, label=f'SPF = {SPF:.2f}')
    plt.plot(days, COP_carnot, label='Carnot COP')


    plt.xlabel('Day')
    plt.ylabel('COP')
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.plot(days, Q_house, label='Heat Demand (W)')
    plt.plot(days, W_required, label='Compressor Power Required (W)')
    plt.xlabel('Day')
    plt.ylabel('Power (W)')
    plt.grid(True)
    plt.legend()
    plt.show()

peterFunc(np.array(getTambs()))

def main():
    Tambs = getTambs()
    for temp in Tambs:
        if temp>17:
            Q = getQtot(temp)
            #COPe = getCOPe()
            #W = Q/COPe