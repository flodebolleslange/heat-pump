import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import numpy as np
from ts_plotter import plot_refridgerant_cycle
import polars as pl

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
        self.ambient_temps = resultdf["temp"].to_list()
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
        self.temp = self.ambient_temps[self.index]/10
        self.time = self.times[self.index]
        self.date = self.dates[self.index]

class Thermostat():

    def __init__(self, file=None, thermostat_type='simple'):
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

        self.thermostat_type = thermostat_type
        if thermostat_type == "simple":
            # force the heatpump off
            self.off_temp = 20.0
            # force the heatpump on
            self.on_temp = 15.0
        elif thermostat_type == "daily":
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
        if self.thermostat_type == 'daily':
            if self.index >= len(self.setting[0])-1 and self.midnight_check == False:
                print("last change of the day")
                print(time)
                self.list_overflow = True
            # if time is after the last item in settings and we haven't gone over midnight and we're not at max index
            if self.midnight_check == False and self.list_overflow == False and (time > self.setting[0][self.index+1]):
                self.index += 1
                print("daytime")
                print(time)
            # if we've gone back in hours then we've gained a day - midnight has passed
            elif time < self.last_time:
                print("past midnight")
                print(time)
                self.midnight_check = True
            # if we've gone past midnight, reset the counter 
            elif time > self.setting[0][0] and self.midnight_check == True:
                self.index=0
                self.list_overflow = False
                self.midnight_check = False
                print("morning")
                print(time)

            # set the on and off temperatures
            self.on_temp = self.setting[1][self.index]
            self.off_temp = self.setting[2][self.index]

        # save the last time so we can detect midnight
        self.last_time = time

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
        self.thermostat = Thermostat(file=r"C:\Users\simon\Code\git\heat-pump\thermostat-setting.csv", thermostat_type='daily')

        # set up heat pump
        # power of the heat pump may change.
        self.heatpump_power = 3000
        # false if heat pump is turned off
        self.heatpump = False
        self.weather = Weather(r'C:\Users\simon\Code\git\heat-pump\weather-raw.csv')

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
        air_reference = self.weather.temp*self.kair/self.thermal_coeff
        ground_reference = self.weather.ground_temp*self.kground/self.thermal_coeff
        temp_in = self.heatpump_power/(self.heat_capacity*self.thermal_coeff)
        
        if self.heatpump == True:
            coefficient = temp_in + ground_reference + air_reference
        else:
            coefficient = ground_reference + air_reference

        self.temp = coefficient + (self.temp - coefficient) * np.e**(-delta_t*self.thermal_coeff*3600)
    
    def timestep(self):
        """Models the heat pump over a timestep. Turns on/off using thermostat."""
        # decides whether the heat pump needs to be on or off
        self.thermostat.update(self.weather.time)
        # activate or deactivate 
        if self.temp > self.thermostat.off_temp:
            self.heatpump = False
        elif self.temp < self.thermostat.on_temp:
            self.heatpump = True
        
        delta_t = self.weather.find_timestep()
        self.find_next_temp(delta_t)
        self.temps.append(self.temp)
        if self.heatpump == True:
            # find the cost of running the heatpupmp with fluctuating electricity prices
            self.heatpump_usage.append(self.heatpump_power*delta_t)
            self.electricity_costs.append(self.heatpump_power*delta_t*self.weather.electricity_price)
        else:
            self.heatpump_usage.append(0)
            self.electricity_costs.append(0)    
        self.weather.update()      

    def iterate(self, start_date, end_date):
        """finds heat pump usage in a specified date range"""

        # storage for generating graphs
        self.temps = []
        self.heatpump_usage = []
        self.electricity_costs = []

        self.weather.unpack_temps(start_date, end_date)
        for n in range(len(self.weather.times)-1):
            self.timestep()

        plt.plot(np.linspace(0,len(self.weather.ambient_temps)/48,num=len(self.weather.times)-1),self.temps,color='blue',label='house temp')
        plt.plot(np.linspace(0,len(self.weather.ambient_temps)/48,num=len(self.weather.times)-1),[n/10 for n in self.weather.ambient_temps[:-1]],color='orange',label='ambient temp')
        plt.xlabel('days')
        plt.ylabel('house temp')
        plt.legend()
        plt.show()

house = House()
house.iterate("2026-05-01","2026-06-01")