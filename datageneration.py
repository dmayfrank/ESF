import pandas as pd
import numpy as np
from tqdm import tqdm


### load data
def load_external_data(settings):
    """load external data.

    Arguments:
        settings -- dictionary of settings

    Returns:
        timeseries_ref -- dataframe with timeseries data from historical reference year
        estimates_2030 -- dataframe with estimated key values (total generation, load, etc.) for the year 2030


    Side effects:
        None
    """
    timeseries_ref = pd.read_csv('./data/external_data/time_series_60min_singleindex.csv', sep = ',', header = 0, index_col=1)               # import timeseries data
    columns = ['DE_solar_capacity','DE_solar_profile','DE_wind_capacity','DE_wind_profile','DE_load_actual_entsoe_transparency'
               ,'DE_wind_onshore_profile','DE_wind_offshore_profile','FR_load_actual_entsoe_transparency'
               ,'FR_solar_generation_actual','FR_wind_onshore_generation_actual','NL_load_actual_entsoe_transparency'
               ,'NL_solar_generation_actual','NL_wind_generation_actual']                                                       # specify which columns to keep
    timeseries_ref = timeseries_ref[columns]                                                                                  # filter columns
    
    if settings['reference_year'] == '2019':
        timeseries_ref = timeseries_ref.iloc[35064-24:43824-24,:]                                                                 # keep only 2019
    elif settings['reference_year'] == '2017':
        timeseries_ref = timeseries_ref.iloc[17543:17543+8760,:]
    elif settings['reference_year'] == '2016-2018':
        timeseries_ref = timeseries_ref.iloc[13127:13127+8760*2,:]                                                              # keep 2017 and half of 2016 and 2018
    
    timeseries_ref = timeseries_ref.astype(float)
    
    estimates_2030 = pd.read_excel('./data/external_data/estimates_2030.xlsx', header=0, index_col=0)
    estimates_2030 = estimates_2030.iloc[14:,:]                                                                                 # keep only relevant rows
    estimates_2030 = estimates_2030.astype(float)
    
    return timeseries_ref, estimates_2030

### create estimated timeseries for 2030
def create_2030_timeseries(settings, timeseries_ref, estimates_2030):
    """create 2030 timeseries data.

    Arguments:
        settings -- dictionary of settings
        timeseries_ref -- dataframe with timeseries data from historical reference year
        estimates_2030 -- dataframe with estimated key values (total generation, load, etc.) for the year 2030

    Returns:
        timeseries_2030 -- dataframe with timeseries data for 2030

    Side effects:
        if settings['export_2030_timeseries'] == True, generated timeseries data will be exported to a csv-file
    """
    timeseries_2030 = pd.DataFrame(columns=['DE_wind','DE_wind_onshore','DE_wind_offshore','DE_solar','DE_otherRE','DE_fossil','DE_nuclear','DE_load'
                                            ,'FR_wind','FR_wind_onshore','FR_wind_offshore','FR_solar','FR_otherRE','FR_fossil','FR_nuclear','FR_load'
                                            ,'NL_wind','NL_wind_onshore','NL_wind_offshore','NL_solar','NL_otherRE','NL_fossil','NL_nuclear','NL_load']
                                   ,index=settings['timesteps'])
    
    if settings['reference_year'] == '2016-2018':
        num_years = 2
    else:
        num_years = 1
    
    # fill columns with constant values each timestep
    timeseries_2030['DE_otherRE'] = estimates_2030.loc['otherRE','DE']/(24*365)
    timeseries_2030['DE_fossil'] = estimates_2030.loc['fossil','DE']/(24*365)
    timeseries_2030['DE_nuclear'] = 0
    timeseries_2030['FR_otherRE'] = estimates_2030.loc['otherRE','FR']/(24*365)
    timeseries_2030['FR_fossil'] = estimates_2030.loc['fossil','FR']/(24*365)
    timeseries_2030['FR_nuclear'] = estimates_2030.loc['nuclear','FR']/(24*365)
    timeseries_2030['NL_otherRE'] = estimates_2030.loc['otherRE','NL']/(24*365)
    timeseries_2030['NL_fossil'] = estimates_2030.loc['fossil','NL']/(24*365)
    timeseries_2030['NL_nuclear'] = estimates_2030.loc['nuclear','NL']/(24*365)
    
    # fill columns with variable values each timestep
    timeseries_2030['DE_wind_onshore'] = list(timeseries_ref['DE_wind_onshore_profile']/timeseries_ref['DE_wind_onshore_profile'].sum()*estimates_2030.loc['wind_onshore','DE']*num_years)
    timeseries_2030['DE_wind_offshore'] = list(timeseries_ref['DE_wind_offshore_profile']/timeseries_ref['DE_wind_offshore_profile'].sum()*estimates_2030.loc['wind_offshore','DE']*num_years)
    timeseries_2030['DE_wind'] = timeseries_2030['DE_wind_onshore'] + timeseries_2030['DE_wind_offshore']
    timeseries_2030['DE_solar'] = list(timeseries_ref['DE_solar_profile']/timeseries_ref['DE_solar_profile'].sum()*estimates_2030.loc['solar','DE']*num_years)
    timeseries_2030['DE_load'] = list(timeseries_ref['DE_load_actual_entsoe_transparency']/timeseries_ref['DE_load_actual_entsoe_transparency'].sum()*estimates_2030.loc['load','DE']*num_years)
    
    timeseries_2030['FR_wind'] = list(timeseries_ref['FR_wind_onshore_generation_actual'] * (estimates_2030.loc['wind','FR']/timeseries_ref['FR_wind_onshore_generation_actual'].sum()*num_years) )
    timeseries_2030['FR_wind_onshore'] = 0
    timeseries_2030['FR_wind_offshore'] = 0
    timeseries_2030['FR_solar'] = list(timeseries_ref['FR_solar_generation_actual'] * (estimates_2030.loc['solar','FR']/timeseries_ref['FR_solar_generation_actual'].sum()*num_years) )
    timeseries_2030['FR_load'] = list(timeseries_ref['FR_load_actual_entsoe_transparency']/timeseries_ref['FR_load_actual_entsoe_transparency'].sum()*estimates_2030.loc['load','FR']*num_years)
    
    timeseries_2030['NL_wind'] = list(timeseries_ref['NL_wind_generation_actual'] * (estimates_2030.loc['wind','NL']/timeseries_ref['NL_wind_generation_actual'].sum()*num_years) )
    timeseries_2030['NL_wind_onshore'] = 0
    timeseries_2030['NL_wind_offshore'] = 0
    timeseries_2030['NL_solar'] = list(timeseries_ref['NL_solar_generation_actual'] * (estimates_2030.loc['solar','NL']/timeseries_ref['NL_solar_generation_actual'].sum()*num_years) )
    timeseries_2030['NL_load'] = list(timeseries_ref['NL_load_actual_entsoe_transparency']/timeseries_ref['NL_load_actual_entsoe_transparency'].sum()*estimates_2030.loc['load','NL']*num_years)
    
    # get missing data by using the data from the same column from one week earlier (7*24 timesteps)
    for i in tqdm(range(len(timeseries_2030)), ascii=True, desc='Estimating missing values while creating timeseries_2030 dataframe:'):
        for j in range(len(timeseries_2030.columns)):
            if np.isnan(timeseries_2030.iloc[i,j]):
                timeseries_2030.iloc[i,j] = timeseries_2030.iloc[i-7*24,j]
    print( 'While creating timeseries_2030 dataframe, ' + str(timeseries_2030.isnull().sum().sum()) + ' missing values have been estimated by taking the values from the same hour one week prior.' )

    timeseries_2030['DE_EE_sum'] = timeseries_2030['DE_wind'] + timeseries_2030['DE_solar'] + timeseries_2030['DE_otherRE'] + timeseries_2030['DE_fossil'] + timeseries_2030['DE_nuclear']
    timeseries_2030['FR_EE_sum'] = timeseries_2030['FR_wind'] + timeseries_2030['FR_solar'] + timeseries_2030['FR_otherRE'] + timeseries_2030['FR_fossil'] + timeseries_2030['FR_nuclear']
    timeseries_2030['NL_EE_sum'] = timeseries_2030['NL_wind'] + timeseries_2030['NL_solar'] + timeseries_2030['NL_otherRE'] + timeseries_2030['NL_fossil'] + timeseries_2030['NL_nuclear']

    # export data
    if settings['export_2030_timeseries'] == True:
        timeseries_2030.to_csv(str('./data/internal_data/timeseries_2030_ref_'+settings['reference_year']+'.csv'), sep=',')

    return timeseries_2030

### load estimated timeseries for 2030
def load_2030_timeseries(settings):
    """load 2030 timeseries data.

    Arguments:
        settings -- dictionary of settings

    Returns:
        timeseries_2030 -- dataframe with timeseries data for 2030

    Side effects:
        None
    """
    timeseries_2030 = pd.read_csv(str('./data/internal_data/timeseries_2030_ref_'+settings['reference_year']+'.csv'), sep = ',', header = 0, index_col=0)
    return timeseries_2030

### get costs
def get_costs(settings):
    c = dict()
    # operational costs
    c['EE_wind'] = 46           # euro/MWh
    c['EE_wind_onshore'] = 46   # euro/MWh
    c['EE_wind_offshore'] = 46  # euro/MWh
    c['EE_solar'] = 51          # euro/MWh
    c['EE_otherRE'] = 70        # euro/MWh
    c['EE_fossil'] = 70         # euro/MWh
    c['EE_nuclear'] = 164       # euro/MWh
    c['EE_import'] = 1000       # euro/MWh; extra teuer, damit möglichst viel über elektrolye gelöst wird.
    c['EE_export'] = 50         # euro/MWh; eher billig
    c['H_import'] = 1000        # euro/MWh; extra teuer, damit möglichst viel über elektrolye gelöst wird.
    c['H_export'] = 50          # euro/MWh; eher billig
    c['GtP'] = 30               # euro/MWh
    c['PtG'] = 30               # euro/MWh
    c['H'] = 0                  # euro/MWh
    c['ET'] = 10                # euro/(MWh*km)
    c['HT'] = 1                 # euro/(MWh*km)
    # investment costs
    c['HL'] = 0                 # euro/(MWh*jahr)
    c['GtPL'] = 5               # euro/(MWh*jahr)
    c['PtGL'] = 5               # euro/(MWh*jahr)
    c['ETL'] = 50               # euro/(MWh*jahr)
    c['HTL'] = 1                # euro/(MWh*jahr)
    return c

### get efficiencies
def get_efficiencies(settings):
    eta = dict()
    eta['electrolysis'] = 0.84
    eta['fuelcell'] = 0.6
    return eta

### get ramps
def get_ramps(settings):
    ramp = dict()
    ramp['electrolysis'] = 1
    ramp['fuelcell'] = 1
    return ramp
    
    
