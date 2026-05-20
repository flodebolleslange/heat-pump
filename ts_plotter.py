import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import numpy as np

def plot_refridgerant_cycle(tim, T1r, T2r, T3r, T4r, p1, p2):
    
    x1, x3 = None # dryness at 1 & 3

    T_sat1 = CP.PropsSI('T', 'Q', 0, 'P', p1, 'R134a')
    T_superheat = T1r - T_sat1
    T_sat2 = CP.PropsSI('T', 'Q', 0, 'P', p2, 'R134a')
    T_subcool = T_sat2 - T3r

    if T_superheat < 0.01:
        x1 = 1 # saturated vapor
        S1 = CP.PropsSI('S', 'T', T1r, 'Q', 1, 'R134a')
        H1 = CP.PropsSI('H', 'T', T1r, 'Q', 1, 'R134a')
    else:
        S1 = CP.PropsSI('S', 'T', T1r, 'P', p1, 'R134a')
        H1 = CP.PropsSI('H', 'T', T1r, 'P', p1, 'R134a')
    if T_subcool < 0.01:
        x3 = 0 # saturated liquid
        S3 = CP.PropsSI('S', 'T', T3r, 'Q', 0, 'R134a')
        H3 = CP.PropsSI('H', 'T', T3r, 'Q', 0, 'R134a')
    else:
        S3 = CP.PropsSI('S', 'T', T3r, 'P', p2, 'R134a')
        H3 = CP.PropsSI('H', 'T', T3r, 'P', p2, 'R134a')

    S2 = CP.PropsSI('S', 'T', T2r, 'P', p2, 'R134a')
    H2 = CP.PropsSI('H', 'T', T2r, 'P', p2, 'R134a')
    H4 = H3
    S4 = CP.PropsSI('S', 'T', T4r, 'P', p1, 'R134a') # could check agreement here - overspecifiied when pressure loss assumed to be zero
    
    




