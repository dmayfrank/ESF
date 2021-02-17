### imports
import pandas as pd
import numpy as np
from tqdm import tqdm
import pickle

import datageneration
import grb_model
import helperfun

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.style as style
style.use('fivethirtyeight')

# Enable high resolution plots
from IPython.display import set_matplotlib_formats
set_matplotlib_formats('retina')


### settings
settings = dict()

# process flow settings
settings['generate_2030_timeseries'] = False # options: True, False # if True, new timeseries data will be generated, if False it will be loaded from csv file

# model settings
settings['countries'] = ['DE', 'FR', 'NL']  # list of countries which the model will consider
settings['neighbours'] = [('DE', 'FR'),('DE','NL')]
settings['electricity_sources'] = ['wind','wind_onshore','wind_offshore','solar','otherRE','fossil','nuclear']

# data generation settings
settings['reference_year'] = '2016-2018'    # options: '2017', '2019', '2016-2018'  # year from which historical data is taken and scaled to fit the year 2030
settings['export_2030_timeseries'] = True   # options: True, False                  # if True, generated timeseries data will be exported to a csv-file
settings['export_calculated_limits'] = True # options: True, False                  # if True, calculated optimal limits will be exported to a csv-file and pickle-file
settings['export_results'] = True           # options: True, False                  # if True, results will be exportet to a pickle file

if settings['reference_year'] == '2016-2018':
    settings['timesteps'] = range(24*365*2)          # range object of all timesteps that will be considered by the model
else:
    settings['timesteps'] = range(24*365)            # range object of all timesteps that will be considered by the model

# plot settings
settings['plot_variables'] = ['H','GtP','PtG','EI','EX','HT','ET','HTL','ETL','GtPL','PtGL','HL']         # options: 'H','GtP','PtG','EI','EX','HT','ET'


### get inputs
# get timeseries_2030 data
if settings['generate_2030_timeseries'] == True:
    timeseries_ref, estimates_2030 = datageneration.load_external_data(settings)
    timeseries_2030 = datageneration.create_2030_timeseries(settings, timeseries_ref, estimates_2030)
else:
    timeseries_2030 = datageneration.load_2030_timeseries(settings)



# make model inputs
T = settings['timesteps']
S = settings['countries']
S_neighbours = settings['neighbours']
EE = helperfun.make_EE_dict(settings, timeseries_2030)
EV = helperfun.make_EV_dict(settings, timeseries_2030)
c = datageneration.get_costs(settings)
eta = datageneration.get_efficiencies(settings)
ramp = datageneration.get_ramps(settings)

### solve model
model, V, C = grb_model.solve_basismodell(T, S, S_neighbours, EE, EV, c, eta, ramp)

### restructure and export results
V_df = helperfun.make_V_df_from_V_dict(settings, V)                 # get variables as dataframes

if settings['reference_year'] == '2016-2018':
    # save objective values of two year optimization in C_twoyear and keep only results of 2030 in C
    C_twoyear = C.copy()
    
    C = dict()
    C['v'] = dict()
    C['f'] = dict()
    for t in tqdm(list(T)[int(8760/2):int(-8760/2)], ascii=True, desc='calculating variable costs:'):        
        for s in S:
            C['v'][t,s] = EE[t,s]['fossil']*c['EE_fossil'] + EE[t,s]['solar']*c['EE_solar'] \
            + EE[t,s]['wind']*c['EE_wind'] + EE[t,s]['wind_onshore']*c['EE_wind_onshore'] + EE[t,s]['wind_offshore']*c['EE_wind_offshore'] \
            + EE[t,s]['otherRE']*c['EE_otherRE'] + EE[t,s]['nuclear']*c['EE_nuclear'] \
            + V_df['EI'].loc[t,s]*c['EE_import'] - V_df['EX'].loc[t,s]*c['EE_export'] \
            + V_df['GtP'].loc[t,s]*c['GtP'] + V_df['PtG'].loc[t,s]*c['PtG'] + V_df['H'].loc[t,s]*c['H'] \
            + 0.5 * sum( c['ET']*V['ETP'][t,(s,s2)] + c['HT']*V['HTP'][t,(s,s2)] for s2 in S if s2 != s ) \
            + 0.5 * sum( -c['ET']*V['ETN'][t,(s,s2)] - c['HT']*V['HTN'][t,(s,s2)] for s2 in S if s2 != s )                                 # (2) - variable costs calculation
    C_v = sum( sum( C['v'][t,s] for s in S )  for t in list(T)[int(8760/2):int(-8760/2)] )
    
    print('calculating investment costs')
    for s in S:
        C['f'][s] = c['HL']*V['HL'][s][0] + c['GtPL']*V['GtPL'][s][0] + c['PtGL']*V['PtGL'][s][0] \
        + sum( c['ETL']*V['ETL'][(s,s2)] + c['HTL']*V['HTL'][(s,s2)] for s2 in S if s2 != s )   
    C_f = sum( C['f'][s] for s in S )
    
    print(str( 'Variable costs: '+str(C_v)+'; Investment costs: '+str(C_f)+'; Sum: '+str(C_v+C_f) ))
    
    # save results of two year optimization in V_df_twoyear and keep only results of 2030 in V_df
    V_df_twoyear = V_df.copy()
    for key in ['H','GtP','PtG','EI','EX','HT','ET']:
        V_df[key] = V_df[key].iloc[int(8760/2):int(-8760/2),:]
        V_df[key].index = list(range(8760))


if settings['export_calculated_limits'] == True:                    # export calculated optimal limits
    for V_key in tqdm(['HTL','ETL','GtPL','PtGL','HL'], ascii=True, desc='Exporting calculated optimal limits to .csv:'):
        V_df[V_key].to_csv(str('./data/internal_data/optimal_limits/'+V_key+'.csv'), sep=',')
    pickle.dump( V, open( './data/internal_data/optimal_limits/limits.p', "wb" ) )          # export as pickle

if settings['export_results'] == True:
    pickle.dump( V, open( './data/internal_data/results/Basismodell/V.p', "wb" ) )          # export as pickle
    pickle.dump( V_df, open( './data/internal_data/results/Basismodell/V_df.p', "wb" ) )    # export as pickle
    pickle.dump( C, open( './data/internal_data/results/Basismodell/C.p', "wb" ) )          # export as pickle
    if settings['reference_year'] == '2016-2018':
        pickle.dump( V_df_twoyear, open( './data/internal_data/results/Basismodell/V_df_twoyear.p', "wb" ) )    # export as pickle
        pickle.dump( C_twoyear, open( './data/internal_data/results/Basismodell/C_twoyear.p', "wb" ) )          # export as pickle
    for key in ['H','GtP','PtG','EI','EX','HT','ET','HTL','ETL','GtPL','PtGL','HL']:
        V_df[key].to_csv(str('./data/internal_data/results/Basismodell/CSVs/'+key+'.csv'), sep=',')
        V_df[key].to_excel(str('./data/internal_data/results/Basismodell/XLSXs/'+key+'.xlsx'))

### plot results
for V_key in settings['plot_variables']:
    if V_key in ['H','GtP','PtG','EI','EX']:
        helperfun.plot_dataframe(V_df[V_key][['DE', 'FR', 'NL']], str(V_key+' values for each country' ), 'timesteps', str(V_key+' values' ), 'best', ['DE','FR', 'NL'])
    elif V_key in ['HT','ET']:
        helperfun.plot_dataframe(V_df[V_key], str(V_key+' values for each pair of countries' ), 'timesteps', 'values', 'best', V_df[V_key].columns)
    else:
        print(str('Plotting the '+V_key+' variable has not been implemented yet.'))

