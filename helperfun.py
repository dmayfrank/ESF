import pandas as pd
import numpy as np
from tqdm import tqdm
import pickle

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.style as style
style.use('fivethirtyeight')

# Enable high resolution plots
from IPython.display import set_matplotlib_formats
set_matplotlib_formats('retina')

def plot_dataframe(df, plot_title, x_name, y_name, legend_loc, legend_labels):
    """plot a dataframe using the given specifications

    options for legend_loc: best, upper right, upper left, lower left, lower right, right, center left, center right, lower center, upper center, center
        
    example: helperfun.plot_dataframe(timeseries_2030[['DE_load', 'DE_wind']], 'Titel', 'timesteps', 'load and wind', 'lower right', ['load','wind'])
    """
    ax = sns.lineplot(data=df)
    ax.set(xlabel=x_name, ylabel=y_name)
    plt.title(plot_title)
    plt.legend(loc=legend_loc, labels=legend_labels)
    #plt.xticks(rotation=45)
    plt.show(ax)
    return None

def make_EE_dict(settings, timeseries_2030):
    """make EE dictionary.

    Arguments:
        settings -- dictionary of settings
        timeseries_2030 -- dataframe with timeseries data for 2030

    Returns:
        EE -- dictionary with hourly electricity generation data for each country

    Side effects:
        None
    """
    EE = dict()
    for t in tqdm(settings['timesteps'], ascii=True, desc='generation of EE dictionary'):
        for s in settings['countries']:
            EE[t,s] = dict()
            EE[t,s]['sum'] = timeseries_2030.loc[t, s+'_EE_sum']
            for source in settings['electricity_sources']:
                EE[t,s][source] = timeseries_2030.loc[t, s+'_'+source]
    return EE

def make_EV_dict(settings, timeseries_2030):
    """make EV dictionary.

    Arguments:
        settings -- dictionary of settings
        timeseries_2030 -- dataframe with timeseries data for 2030

    Returns:
        EV -- dictionary with hourly electricity demand data for each country

    Side effects:
        None
    """
    EV = dict()
    for t in tqdm(settings['timesteps'], ascii=True, desc='generation of EV dictionary'):
        for s in settings['countries']:
            EV[t,s] = timeseries_2030.loc[t, s+'_load']
    return EV

def make_V_df_from_V_dict(settings, V):
    """make dataframes out of gurobi variable solutions, which come as dictionaries.

    Arguments:
        settings -- dictionary of settings
        V -- dictionary of dictionaries with all optimal variable values

    Returns:
        EV -- dictionary of dataframes with all optimal variable values

    Side effects:
        None
    """
    S_neighbours = settings['neighbours']
    V_df = dict()
    for V_key in settings['plot_variables']:
        if V_key in ['H','GtP','PtG','EI','EX']:
            V_df[V_key] = pd.DataFrame(columns=['DE', 'FR', 'NL'], index=range(8760))
            for (row, column), value in tqdm( V[V_key].items(), ascii=True, desc=str('building '+V_key+' dataframe from '+V_key+' dict' )):
                V_df[V_key].loc[row, column] = value
            V_df[V_key] = V_df[V_key].astype('float')
        elif V_key in ['HT','ET']:
            V_df[V_key] = pd.DataFrame(columns=[str(x[0]+' --> '+x[1]) for x in S_neighbours], index=range(8760))
            for (row, (s1,s2)), value in tqdm( V[V_key].items(), ascii=True, desc=str('building '+V_key+' dataframe from '+V_key+' dict' )):
                if (s1,s2) in S_neighbours:
                    V_df[V_key].loc[row, str(s1+' --> '+s2)] = value
            V_df[V_key] = V_df[V_key].astype('float')
        elif V_key in ['HTL','ETL']:
            print(str('building '+V_key+' dataframe from '+V_key+' dictionary'))
            V_df[V_key] = dict()
            for (s1,s2), value in V[V_key].items():
                V_df[V_key][str(s1+' --> '+s2)] = [value]
            V_df[V_key] = pd.DataFrame.from_dict(V_df[V_key])
        elif V_key in ['GtPL','PtGL','HL']:
            print(str('building '+V_key+' dataframe from '+V_key+' dictionary.'))
            V[V_key] = {k: [v] for k, v in V[V_key].items()}
            V_df[V_key] = pd.DataFrame.from_dict(V[V_key])
        else:
            print(str('Building a dataframe for the '+V_key+' variable has not been implemented yet.'))
    return V_df
    
def get_limits(settings):
    """get limits for rolling horizon optimization.

    Arguments:
        settings -- dictionary of settings
        V -- dictionary of dictionaries with all optimal variable values

    Returns:
        EV -- dictionary of dataframes with all optimal variable values

    Side effects:
        None
    """
    if settings['limits_source'] == 'basismodell':
        limits = pickle.load( open( './data/internal_data/optimal_limits/limits.p', "rb" ) )
        HTL = limits['HTL']
        ETL = limits['ETL']
        GtPL = {k: v[0] for k, v in limits['GtPL'].items()}
        PtGL = {k: v[0] for k, v in limits['PtGL'].items()}
        HL = {k: v[0] for k, v in limits['HL'].items()}
    elif settings['limits_source'] == 'recherche':
        print("settings['limits_source'] == 'recherche' wurde noch nicht implementiert")
    else:
        print("Bitte checke settings['limits_source'] in master_RH.py und die gegebenen Optionen.")
    return HTL, ETL, GtPL, PtGL, HL