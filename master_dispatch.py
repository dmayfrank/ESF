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
settings['generate_2030_timeseries'] = False        # options: True, False # if True, new timeseries data will be generated, if False it will be loaded from csv file

# model settings
settings['countries'] = ['DE', 'FR', 'NL']          # list of countries which the model will consider
settings['neighbours'] = [('DE', 'FR'),('DE','NL')]
settings['electricity_sources'] = ['wind','wind_onshore','wind_offshore','solar','otherRE','fossil','nuclear']

# data generation settings
settings['reference_year'] = '2017'                 # options: '2017', '2019', '2016-2018'      # year from which historical data is taken and scaled to fit the year 2030
settings['export_2030_timeseries'] = False          # options: True, False  # if True, generated timeseries data will be exported to a csv-file
settings['export_results'] = True                   # options: True, False  # if True, results will be exportet to a pickle file

if settings['reference_year'] == '2016-2018':
    settings['timesteps'] = range(24*365*2)         # range object of all timesteps that will be considered by the model
else:
    settings['timesteps'] = range(24*365)           # range object of all timesteps that will be considered by the model

# plot settings
settings['plot_variables'] = ['H','GtP','PtG','EI','EX','HT','ET']         # options: 'H','GtP','PtG','EI','EX','HT','ET'

# settings specific to rolling horizon model
settings['limits_source'] = 'basismodell'                                  # options: 'basismodell', 'recherche'


### get inputs
# get timeseries_2030 data
if settings['generate_2030_timeseries'] == True:
    timeseries_ref, estimates_2030 = datageneration.load_external_data(settings)
    timeseries_2030 = datageneration.create_2030_timeseries(settings, timeseries_ref, estimates_2030)
else:
    timeseries_2030 = datageneration.load_2030_timeseries(settings)



# make model inputs
T = list(settings['timesteps'])
S = settings['countries']
S_neighbours = settings['neighbours']
EE = helperfun.make_EE_dict(settings, timeseries_2030)
EV = helperfun.make_EV_dict(settings, timeseries_2030)
c = datageneration.get_costs(settings)
eta = datageneration.get_efficiencies(settings)
ramp = datageneration.get_ramps(settings)
HTL, ETL, GtPL, PtGL, HL = helperfun.get_limits(settings)
H0 = {s: 0 for s in S}                                                      # each country has 0 H2 stored in t = 0

### solve model
model, V, C = grb_model.solve_dispatch(T, S, S_neighbours, EE, EV, c, eta, ramp,
                              HTL, ETL, GtPL, PtGL, HL, H0, last_step=True, rolling_horizon=False, print_result=True)

### make solution dataframe
V_df = dict()
for V_key in ['H','GtP','PtG','EI','EX','HT','ET']:
    if V_key in ['H','GtP','PtG','EI','EX']:
        V_df[V_key] = pd.DataFrame(columns=['DE', 'FR', 'NL'], index=T)
    elif V_key in ['HT','ET']:
        V_df[V_key] = pd.DataFrame(columns=[str(x[0]+' --> '+x[1]) for x in S_neighbours], index=T)

for t_save in tqdm(T, ascii=True, desc='saving results of dispatch optimization in dataframe V_df:'):                      # save results in V_df
    for V_key in ['H','GtP','PtG','EI','EX','HT','ET']:
        if V_key in ['H','GtP','PtG','EI','EX']:
            for s in S:
                V_df[V_key][s][t_save] = V[V_key][t_save, s]
        elif V_key in ['HT','ET']:
            for (s1,s2) in S_neighbours:
                V_df[V_key][str(s1+' --> '+s2)][t_save] = V[V_key][t_save, (s1,s2)]

for V_key in ['H','GtP','PtG','EI','EX','HT','ET']:
    V_df[V_key] = V_df[V_key].astype('float')

if settings['reference_year'] == '2016-2018':
    # save results of two year optimization in V_df_twoyear and keep only results of 2030 in V_df
    V_df_twoyear = V_df.copy()
    for key in ['H','GtP','PtG','EI','EX','HT','ET']:
        V_df[key] = V_df[key].iloc[int(8760/2):int(-8760/2),:]
        V_df[key].index = list(range(8760))

### calculate objective value result
if settings['reference_year'] == '2016-2018':
    C_v = sum( sum( C['v'][t,s] for s in S )  for t in T[int(8760/2):int(-8760/2)] )
else:
    C_v = sum( sum( C['v'][t,s] for s in S )  for t in T )

C['f'] = dict()
for s in S:
    C['f'][s] = c['HL']*HL[s] + c['GtPL']*GtPL[s] + c['PtGL']*PtGL[s] \
    + sum( c['ETL']*ETL[(s,s2)] + c['HTL']*HTL[(s,s2)] for s2 in S if s2 != s )   
C_f = sum( C['f'][s] for s in S )

print(str( 'Variable costs: '+str(C_v)+'; Investment costs: '+str(C_f)+'; Sum: '+str(C_v+C_f) ))

### export results
if settings['export_results'] == True:
    pickle.dump( V_df, open( './data/internal_data/results/Dispatchmodell/V_df.p', "wb" ) )    # export as pickle
    pickle.dump( C, open( './data/internal_data/results/Dispatchmodell/C.p', "wb" ) )          # export as pickle
    if settings['reference_year'] == '2016-2018':
        pickle.dump( V_df_twoyear, open( './data/internal_data/results/Dispatchmodell/V_df_twoyear.p', "wb" ) )    # export as pickle
    for key in ['H','GtP','PtG','EI','EX','HT','ET']:
        V_df[key].to_csv(str('./data/internal_data/results/Dispatchmodell/CSVs/'+key+'.csv'), sep=',')
        V_df[key].to_excel(str('./data/internal_data/results/Dispatchmodell/XLSXs/'+key+'.xlsx'))

### plot results
for V_key in settings['plot_variables']:
    if V_key in ['H','GtP','PtG','EI','EX']:
        helperfun.plot_dataframe(V_df[V_key][['DE', 'FR', 'NL']], str(V_key+' values for each country' ), 'timesteps', str(V_key+' values' ), 'best', ['DE','FR', 'NL'])
    elif V_key in ['HT','ET']:
        helperfun.plot_dataframe(V_df[V_key], str(V_key+' values for each pair of countries' ), 'timesteps', 'values', 'best', V_df[V_key].columns)
    else:
        print(str('Plotting the '+V_key+' variable has not been implemented yet.'))
