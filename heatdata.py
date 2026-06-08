import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import numpy as np
from ts_plotter import plot_refridgerant_cycle
import polars as pl
import CoolProp.CoolProp as cp
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class Weather():
    """A class for defining global variables that affect all houses"""

    def __init__(self, file):
        self.datadf = pl.read_csv(file)
        self.datadf = self.datadf.with_row_index(name='index')
        self.data = pl.SQLContext(data=self.datadf, eager=True)
        self.time = 0
        self.day = 0
        self.month = 0
        self.year = 0
        self.groundtemp = 10.0
        # price per joule
        self.electricity_price = 0.25/(1000*3600)

    def unpack_temps(self, start_date, end_date):
        """returns a list of temperatures and their corresponding times"""
        result_index_start = min(self.data.execute("""SELECT * FROM data WHERE STARTS_WITH(date,'"""+start_date+"""')""")['index'].to_list())
        result_index_end = max(self.data.execute("""SELECT * FROM data WHERE STARTS_WITH(date,'"""+end_date+"""')""")['index'].to_list())
        resultdf = self.data.execute("""SELECT * FROM data WHERE index>"""+str(result_index_start)+""" AND index<"""+str(result_index_end))
        self.ambient_temps = [n/10 for n in resultdf["temp"].to_list()]
        self.dates = resultdf["date"].to_list()
        hours = resultdf["hour"].to_list()
        minutes = resultdf["minute"].to_list()
        seconds = resultdf["second"].to_list()
        self.times = [hours[n]+minutes[n]/60+seconds[n]/3600 for n in range(len(hours))]
        self.index = 0
        self.temp = self.ambient_temps[0]
        self.ground_temp = 11.0

    def find_timestep(self):
        """finds the time difference between the current and next data"""

        # Find the difference in time of day. Assume timesteps are less than 1 day.
        delta_t = self.times[self.index+1]-self.times[self.index]

        # If timestep is negative, we've gone past midnight, so add 24 hours
        if delta_t < 0:
            delta_t += 24

        return delta_t
    
    def update(self):
        """updates weather values for the next timestep"""
        self.index += 1
        self.temp = self.ambient_temps[self.index]
        self.time = self.times[self.index]
        self.date = self.dates[self.index]

class Thermostat():

    def __init__(self, file=None, mode='simple'):
        if file:
            thermostat_datadf = pl.read_csv(file)
            thermostat_datadf = thermostat_datadf.with_row_index(name='index')
            thermostat_data_context = pl.SQLContext(data=thermostat_datadf, eager=True)
            thermostat_data = thermostat_data_context.execute("""SELECT * FROM data""")
            hours = thermostat_data["hour"].to_list()
            minutes = thermostat_data["minute"].to_list()
            seconds = thermostat_data["second"].to_list()
            times = [hours[n]+minutes[n]/60+seconds[n]/3600 for n in range(len(hours))]
            on_temp = thermostat_data["on_temp"]
            off_temp = thermostat_data["off_temp"]

        self.mode = mode
        if mode == "simple":
            # force the heatpump off
            self.off_temp = 20.0
            # force the heatpump on
            self.on_temp = 15.0
        elif mode == "daily":
            self.setting = [times, on_temp, off_temp]
            self.index = 0
        
        # variables for updating
        # time at previous update
        self.last_time = 0.0
        # has there been a midnight since updating thermostat values?
        self.midnight_check = False
        # will [self.index + 1] cause an error?
        self.list_overflow = False

    def update(self, time):
        if self.mode == 'daily':
            if self.index >= len(self.setting[0])-1 and self.midnight_check == False:
                self.list_overflow = True
            # if time is after the last item in settings and we haven't gone over midnight and we're not at max index
            if self.midnight_check == False and self.list_overflow == False and (time > self.setting[0][self.index+1]):
                self.index += 1
            # if we've gone back in hours then we've gained a day - midnight has passed
            elif time < self.last_time:
                self.midnight_check = True
            # if we've gone past midnight, reset the counter 
            elif time > self.setting[0][0] and self.midnight_check == True:
                self.index=0
                self.list_overflow = False
                self.midnight_check = False

            # set the on and off temperatures
            self.on_temp = self.setting[1][self.index]
            self.off_temp = self.setting[2][self.index]

        # save the last time so we can detect midnight
        self.last_time = time

class Heatpump():

    def __init__(self):
        # Heat pump assumptions
        self.radiator = 60.0 # degC
        self.pinch_point = 5 # K
        self.isentropic_efficiency = 0.9

        # false if heat pump is turned off
        self.on = False

        # store data in lists
        self.works = []
        self.heats = []
        self.COPs = []
        self.COP_carnots = []

        # set values so that nothing crashes on first iteration
        self.q_out = 0
        self.work = 0
        self.COP = 3.0
        self.COP_carnot = 0

    def calculate_cycle(self, Tambs):
        # Refrigerant cycle
        Tevap = Tambs - self.pinch_point          # degC, refrigerant colder than ambient
        Tcond = self.radiator + self.pinch_point      # degC, refrigerant hotter than radiator water

        Pcond = CP.PropsSI('P', 'T', Tcond + 273.15, 'Q', 0, 'R134a')

        H1 = CP.PropsSI('H', 'T', Tevap + 273.15, 'Q', 1, 'R134a')
        S1 = CP.PropsSI('S', 'T', Tevap + 273.15, 'Q', 1, 'R134a')

        H2s = CP.PropsSI('H', 'P', Pcond, 'S', S1, 'R134a')
        H2 = H1 + (H2s - H1) / self.isentropic_efficiency

        H3 = CP.PropsSI('H', 'P', Pcond, 'Q', 0, 'R134a')
        H4 = H3

        mass_flow = 0.025361
        q_out = (H2 - H3)*mass_flow
        w_comp = (H2 - H1)*mass_flow

        self.COP = q_out / w_comp
        self.q_out = q_out
        self.work = w_comp
        self.COP_carnot = (Tcond + 273.15) / ((Tcond + 273.15) - (Tevap + 273.15))

class House():

    def __init__(self):
        # house parameters
        self.height = 6.0
        self.length = 9.0
        self.width = 12.0
        self.temp = 20.0
        air_density = 101325/(287*(self.temp+273))
        self.heat_capacity = self.length*self.width*self.height*air_density*1005
        self.getRtot()

        # set up thermostat
        self.thermostat = Thermostat(file=r"thermostat-setting.csv", mode='daily')

        # set up heat pump
        self.heatpump = Heatpump()

        # load weather data
        self.weather = Weather(r'weather-raw.csv')

        # storage for generating graphs
        self.temps = []
        self.heatpump_work = []
        self.electricity_costs = []
        self.heatpump_on_times = []
        self.heatpump_on_ambients = []
        self.heatpump_on_temps = []

    def getRroof(self):
        insulation_thickness = 270.0  # mm
        U = 40.3175 / insulation_thickness  # W/m^2/K
        area = self.length * self.width
        return 1/(U*area)

    def getRfloor(self):
        U_specific = 40.32
        thickness = 30.0
        U = U_specific / thickness
        area = self.length * self.width
        return 1/(U * area)

    def getRwalls(self):
        Rbrick = (1 / 846.67) * 102.5
        Rrockwool = (1 / 40.3175) * 102.5
        Rtot = 2 * Rbrick + Rrockwool

        area_walls = 2 * self.height * self.length \
                + 2 * self.height * self.width

        return Rtot/area_walls

    def getRtot(self):
        Rroof = self.getRroof()
        Rwalls = self.getRwalls()
        Rfloor = self.getRfloor()

        # set the resistances as house attributes
        self.Rair = 1/(1/Rroof+1/Rwalls)
        self.Rground = Rfloor
        self.kground = 1/(self.Rground*self.heat_capacity)
        self.kair = 1/(self.Rair*self.heat_capacity)
        self.thermal_coeff = self.kground + self.kair

    def find_next_temp(self, delta_t):
        """models heat loss in the house over half a timestep"""
        air_reference = self.weather.temp*self.kair/self.thermal_coeff
        ground_reference = self.weather.ground_temp*self.kground/self.thermal_coeff
        temp_in = self.heatpump.q_out/(self.heat_capacity*self.thermal_coeff)
        
        if self.heatpump.on == True:
            coefficient = temp_in + ground_reference + air_reference
        else:
            coefficient = ground_reference + air_reference

        self.temp = coefficient + (self.temp - coefficient) * np.e**(-delta_t*self.thermal_coeff*3600)
    
    def timestep(self):
        """Models the heat pump over a timestep. Turns on/off using thermostat."""
        # update the thermostat temperatures for the current time of day
        self.thermostat.update(self.weather.time)
        # activate or deactivate 
        if self.temp > self.thermostat.off_temp:
            self.heatpump.on = False
        elif self.temp < self.thermostat.on_temp:
            self.heatpump.on = True
        
        # update the weather
        delta_t = self.weather.find_timestep()
        self.find_next_temp(delta_t)
        self.temps.append(self.temp)

        # work out the electricity used and add to list to plot
        if self.heatpump.on == True:
            # update the heatpump cycle
            self.heatpump.calculate_cycle(self.weather.temp)
            self.heatpump.works.append(self.heatpump.work*delta_t)
            self.heatpump.heats.append(self.heatpump.q_out*delta_t)
            # store the COP and Carnot COP
            self.heatpump.COPs.append(self.heatpump.COP)
            self.heatpump.COP_carnots.append(self.heatpump.COP_carnot)
            # save the time that the heatpump turned on
            self.heatpump_on_times.append(self.weather.time)
            self.heatpump_on_ambients.append(self.weather.temp)
            self.heatpump_on_temps.append(self.temp)
        else:
            self.heatpump.works.append(0)
            self.heatpump.heats.append(0)
        # find the cost of running the heatpupmp with fluctuating electricity prices
        self.electricity_costs.append(self.heatpump.work*delta_t*self.weather.electricity_price)

        # set the weather to the next time step
        self.weather.update()      

    def iterate(self, start_date, end_date):
        """finds heat pump usage in a specified date range"""

        self.weather.unpack_temps(start_date, end_date)
        for n in range(len(self.weather.times)-1):
            self.timestep()

        SPF = sum(self.heatpump.heats)/sum(self.heatpump.works)
        print("SPF: ",SPF)

        # creates a list of average COP values over a 24 hour period, ignoring points at which the heat pump is off
        all_cops = [self.heatpump.heats[n]/self.heatpump.works[n] if self.heatpump.heats[n]>0 else 0 for n in range(len(self.heatpump.heats))]
        daily_average_COP = [sum(all_cops[n-48:n+48]) / (len([m for m in all_cops[n-48:n+48] if m != 0])+1) for n in range(len(self.heatpump.works))]
        variable1 = daily_average_COP
        variable2 = self.heatpump.COP_carnots
        plt.plot(np.linspace(0,len(self.weather.ambient_temps)/48,num=len(self.weather.times)-1),variable1,color='blue',label='average COP')
        # plt.plot(np.linspace(0,len(self.weather.ambient_temps)/48,num=len(self.weather.times)-1),variable2,color='orange',label='outside')
        plt.xlabel('days')
        plt.ylabel('temps')
        plt.legend()
        plt.show()

        plt.scatter(self.heatpump_on_times,self.heatpump.COPs,color='blue',label='COP')
        plt.scatter(self.heatpump_on_times,self.heatpump.COP_carnots,color='orange',label='Carnot COP')
        plt.xlabel('hour')
        plt.ylabel('COP')
        plt.legend()
        plt.show()

house = House()
house.iterate("2026-01-01","2026-01-01")