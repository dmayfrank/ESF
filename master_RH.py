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

# data generation settings
settings['reference_year'] = '2016-2018'    # options: '2017', '2019', '2016-2018'      # year from which historical data is taken and scaled to fit the year 2030
settings['export_2030_timeseries'] = False  # options: True, False  # if True, generated timeseries data will be exported to a csv-file
settings['export_results'] = True           # options: True, False  # if True, results will be exportet to a pickle file

# model settings
settings['countries'] = ['DE', 'FR', 'NL']  # list of countries which the model will consider
settings['neighbours'] = [('DE', 'FR'),('DE','NL')]
settings['electricity_sources'] = ['wind','wind_onshore','wind_offshore','solar','otherRE','fossil','nuclear']
if settings['reference_year'] == '2016-2018':
    settings['timesteps'] = range(24*365+24*7*2)        # range object of all timesteps that will be considered by the model
else:
    settings['timesteps'] = range(24*365)               # range object of all timesteps that will be considered by the model

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

if settings['reference_year'] == '2016-2018':
    timeseries_2030 = timeseries_2030.iloc[int(8760/2):int(-8760/2)+24*7*2,:]
    timeseries_2030.index = list(settings['timesteps'])

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
if settings['reference_year'] == '2016-2018':
    H0 = pickle.load( open( './data/internal_data/results/Basismodell/V.p', "rb" ) )
    H0 = {s: H0['H'][int(8760/2),s] for s in S}                                 # each country has as much H2 stored in t = 0 as they have in the same timestep when using the basic model
else:
    H0 = {s: 0 for s in S}                                                      # each country has 0 H2 stored in t = 0 (and t = 8760)

### make solution dataframe
V_df = dict()
for V_key in ['H','GtP','PtG','EI','EX','HT','ET']:
    if V_key in ['H','GtP','PtG','EI','EX']:
        V_df[V_key] = pd.DataFrame(columns=['DE', 'FR', 'NL'], index=range(8760))
    elif V_key in ['HT','ET']:
        V_df[V_key] = pd.DataFrame(columns=[str(x[0]+' --> '+x[1]) for x in S_neighbours], index=range(8760))
    
    
### solve model
t_horizon = 24*7*2                                                          # rolling timehorizon of 2 weeks

for t in tqdm(T[0:-t_horizon], ascii=True, desc='solving rolling horizon optimization:'):
    T_step = T[t:t+t_horizon]

    model, V, _ = grb_model.solve_dispatch(T_step, S, S_neighbours, EE, EV, c, eta, ramp,
                                     HTL, ETL, GtPL, PtGL, HL, H0, last_step=False, rolling_horizon=True, print_result=False)
    H0 = {s: V['H'][(t,s)] for s in S}                                  # update H0 for next timestep
    
    for V_key in ['H','GtP','PtG','EI','EX','HT','ET']:                 # save results of current timestep in V_df
        if V_key in ['H','GtP','PtG','EI','EX']:
            for (_,s),v in V[V_key].items():
                V_df[V_key][s][t] = v
        elif V_key in ['HT','ET']:
            for (_,(s1,s2)),v in V[V_key].items():
                if (s1,s2) in S_neighbours:
                    V_df[V_key][str(s1+' --> '+s2)][t] = v

for V_key in V_df.keys():
    V_df[V_key] = V_df[V_key].astype('float')

### calculate objective value results
C = dict()
C['v'] = dict()
C['f'] = dict()
for t in tqdm(range(8760), ascii=True, desc='calculating variable costs:'):        
    for s in S:
        C['v'][t,s] = EE[t,s]['fossil']*c['EE_fossil'] + EE[t,s]['solar']*c['EE_solar'] \
        + EE[t,s]['wind']*c['EE_wind'] + EE[t,s]['otherRE']*c['EE_otherRE'] + EE[t,s]['nuclear']*c['EE_nuclear'] \
        + V_df['EI'].loc[t,s]*c['EE_import'] - V_df['EX'].loc[t,s]*c['EE_export'] \
        + V_df['GtP'].loc[t,s]*c['GtP'] + V_df['PtG'].loc[t,s]*c['PtG'] + V_df['H'].loc[t,s]*c['H'] \
        + sum( c['ET']*abs(V_df['ET'].loc[t,str(s+' --> '+s2)]) + c['HT']*abs(V_df['HT'].loc[t,str(s+' --> '+s2)]) for s2 in S if (s,s2) in S_neighbours )
C_v = sum( sum( C['v'][t,s] for s in S )  for t in range(8760) )

print('calculating investment costs')
for s in S:
    C['f'][s] = c['HL']*HL[s] + c['GtPL']*GtPL[s] + c['PtGL']*PtGL[s] \
    + sum( c['ETL']*ETL[(s,s2)] + c['HTL']*HTL[(s,s2)] for s2 in S if s2 != s )   
C_f = sum( C['f'][s] for s in S )

print(str( 'Variable costs: '+str(C_v)+'; Investment costs: '+str(C_f)+'; Sum: '+str(C_v+C_f) ))

### export results
if settings['export_results'] == True:
    pickle.dump( V_df, open( './data/internal_data/results/RH_Modell/V_df.p', "wb" ) )    # export as pickle
    pickle.dump( C, open( './data/internal_data/results/RH_Modell/C.p', "wb" ) )          # export as pickle
    for key in ['H','GtP','PtG','EI','EX','HT','ET']:
        V_df[key].to_csv(str('./data/internal_data/results/RH_Modell/CSVs/'+key+'.csv'), sep=',')
        V_df[key].to_excel(str('./data/internal_data/results/RH_Modell/XLSXs/'+key+'.xlsx'))

### plot results
for V_key in settings['plot_variables']:
    if V_key in ['H','GtP','PtG','EI','EX']:
        helperfun.plot_dataframe(V_df[V_key][['DE', 'FR', 'NL']], str(V_key+' values for each country' ), 'timesteps', str(V_key+' values' ), 'best', ['DE','FR', 'NL'])
    elif V_key in ['HT','ET']:
        helperfun.plot_dataframe(V_df[V_key], str(V_key+' values for each pair of countries' ), 'timesteps', 'values', 'best', V_df[V_key].columns)
    else:
        print(str('Plotting the '+V_key+' variable has not been implemented yet.'))
