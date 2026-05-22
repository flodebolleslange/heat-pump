import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import numpy as np
from satline_plot import plot_satline

# currently assumes no pressure loss through condensor/evaporator

def iterate_pressure_loss(p1, p2, T3r, T4r, T_subcool, T_superheat):

    # assume ratio of pressure loss in evaporator to condenser is 3:1 - wild guess
    loss_ratio = 3
    cond_loss = 0
    evap_loss = cond_loss / loss_ratio
    solved = False

    while solved == False:
        p3 = p2 * (1 - cond_loss / 100)
        p4 = p1 * (1 + evap_loss / 100)

        if T_subcool < 1:
            x3 = 0 # saturated liquid
            H3 = CP.PropsSI('H', 'T', T3r, 'Q', x3, 'R134a')
        else:
            H3 = CP.PropsSI('H', 'T', T3r, 'P', p3, 'R134a')

        H4 = H3
        S4 = CP.PropsSI('S', 'P', p4, 'H', H4, 'R134a') # could check agreement here - overspecifiied when pressure loss assumed to be zero
        T4_check = CP.PropsSI('T', 'S', S4, 'H', H4, 'R134a')
        print(abs(T4_check - T4r))
        if abs(T4_check - T4r) < 1 or T4_check > T4r:
            solved = True
            return cond_loss, evap_loss,p1, p2, p3, p4
        else:
            cond_loss += 0.01
            evap_loss = cond_loss / loss_ratio
        print("T4 Check:", T4_check - 273.15)
        print("T4r:", T4r - 273.15)
        

def plot_refridgerant_cycle(tim, T1r, T2r, T3r, T4r, p1, p2):
    
    #x1, x3 = None # dryness at 1 & 3
    fluid = 'R134a'
    (s_satline, T_satline, p_satline, H_satline) = plot_satline(fluid)

    T_sat1 = CP.PropsSI('T', 'Q', 0, 'P', p1, 'R134a')
    T_superheat = T1r - T_sat1
    print("T Superheat:", T_superheat)
    T_sat2 = CP.PropsSI('T', 'Q', 0, 'P', p2, 'R134a')
    T_subcool = T_sat2 - T3r
    print("T Subcool:", T_subcool)

    print(iterate_pressure_loss(p1, p2, T3r, T4r, T_subcool, T_superheat))

    if T_superheat < 1:
        x1 = 1 # saturated vapor
        S1 = CP.PropsSI('S', 'T', T1r, 'Q', x1, 'R134a')
        H1 = CP.PropsSI('H', 'T', T1r, 'Q', x1, 'R134a')
    else:
        S1 = CP.PropsSI('S', 'T', T1r, 'P', p1, 'R134a')
        H1 = CP.PropsSI('H', 'T', T1r, 'P', p1, 'R134a')
    if T_subcool < 1:
        x3 = 0 # saturated liquid
        S3 = CP.PropsSI('S', 'T', T3r, 'Q', x3, 'R134a')
        H3 = CP.PropsSI('H', 'T', T3r, 'Q', x3, 'R134a')
    else:
        S3 = CP.PropsSI('S', 'T', T3r, 'P', p2, 'R134a')
        H3 = CP.PropsSI('H', 'T', T3r, 'P', p2, 'R134a')

    S2 = CP.PropsSI('S', 'T', T2r, 'P', p2, 'R134a')
    H2 = CP.PropsSI('H', 'T', T2r, 'P', p2, 'R134a')
    H4 = H3
    S4 = CP.PropsSI('S', 'P', p1, 'H', H4, 'R134a') # could check agreement here - overspecifiied when pressure loss assumed to be zero
    T4_check = CP.PropsSI('T', 'S', S4, 'H', H4, 'R134a')
    print("T4 Check:", T4_check - 273.15)
    print("T4r:", T4r - 273.15)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14,6), dpi=100)
    ax1.plot(s_satline, T_satline, color='black', linewidth=2)
    ax1.scatter([S1/1000, S2/1000, S3/1000, S4/1000], [T1r -273.15, T2r -273.15, T3r -273.15, T4r -273.15])
    ax1.set_title('T-S Diagram')
    ax1.set_xlabel('Entropy (J/kg-K)')
    ax1.set_ylabel('Temperature (K)')
    ax1.grid()

    ax2.plot(H_satline, p_satline, color='black', linewidth=2)
    ax2.scatter([H1/1000, H2/1000, H3/1000, H4/1000], [p1/1e5, p2/1e5, p2/1e5, p1/1e5])
    ax2.set_title('P-H Diagram')
    ax2.set_xlabel('Enthalpy (J/kg)')
    ax2.set_ylabel('Pressure (Pa)')
    ax2.grid()
    plt.tight_layout()
    plt.show()
