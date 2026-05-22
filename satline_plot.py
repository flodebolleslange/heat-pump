import CoolProp.CoolProp as cp
import numpy as np
import matplotlib.pyplot as plt

def plot_satline(fluid):
    # Find critcal-point and triple-point pressures
    pc = cp.PropsSI (fluid,'pcrit')
    pt = cp.PropsSI (fluid,'ptriple')

    # Create array of pressures with geometric distribution 
    p  = np.geomspace(pt,pc,500)
    # Use the CoolProp routines to get T and s (note Q is same as dryness)
    ts = cp.PropsSI ('T','P',p,'Q',0.0,fluid) - 273.15
    sf = cp.PropsSI ('S','P',p,'Q',0.0,fluid) / 1000
    sg = cp.PropsSI ('S','P',p,'Q',1.0,fluid) / 1000
    hf = cp.PropsSI ('H','P',p,'Q',0.0,fluid) / 1000
    hg = cp.PropsSI ('H','P',p,'Q',1.0,fluid) / 1000

    # Plot both wet and dry sat together (may be a bit flat)
    H = np.concatenate((hf,np.flip(hg)[1:]))
    T = np.concatenate((ts,np.flip(ts)[1:]))
    s = np.concatenate((sf,np.flip(sg)[1:]))
    p = np.concatenate((p/1e5,np.flip(p/1e5)[1:]))

    return (s, T, p, H)


