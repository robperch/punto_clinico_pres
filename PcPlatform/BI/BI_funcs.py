## ANALYZING BUSINESS DATA - FUNCTIONS FILE
#### Author: Rob (GH: Roberto919)
#### Date: 20 July 2020





'------------------------------------------------------------------------------------------'
#############
## Imports ##
#############


## Python libraries

import pandas as pd

import numpy as np

import re

from datetime import *

import plotly.graph_objects as go
from plotly.subplots import make_subplots


import math


## Ancillary modules

from BI_params import *





'------------------------------------------------------------------------------------------'
#######################
## Generic functions ##
#######################


## Function to add week number as string
def add_week_num(row):
    """
    Function to add week number as string
    """

    res = 'No_val'

    week_num = str(datetime.isocalendar(row)[1])

    if len(week_num) == 2:
        res = str(datetime.isocalendar(row)[0]) + '-' + week_num
    else:
        res = str(datetime.isocalendar(row)[0]) + '-' + '0' + week_num

    return res



## Create directory of doctors (based on proccesed dataset 'LISTADETALLADADELASCITAS.csv')
def create_doctors_dir(df):
    """
    Create directory of doctors (based on proccesed dataset 'LISTADETALLADADELASCITAS.csv')
    """

    meds = df['NOMBRE DEL CLÍNICO'].unique()

    meds_dict_ref = {}

    for med in meds:

        meds_dict_ref[med] = {}

        m1 = df['NOMBRE DEL CLÍNICO'] == med
        dfx = df.loc[m1, :]

        meds_dict_ref[med]['Especialidad'] = list(dfx['ASUNTO_sinth'].unique())
        meds_dict_ref[med]['Sitios'] = list(dfx['SITIO'].unique())


    return meds_dict_ref



## Homologate all locations
def homologate_locations(row):
    """
    Homologate all locations
        args:
            row (string): name of raw location
        returns:
            res (string): location with name homologated
    """

    res = 'Location_not_found'
    for loc_h in locations_ref:
        if row in locations_ref[loc_h]:
            res = loc_h

    return res





'------------------------------------------------------------------------------------------'
#####################################################
## Data analysis - Appointments - Cleaning main df ##
#####################################################


## Cleaning imported dataframes - Appointments dataframe
def dfa_clean(dfa):
    """
    Cleaning imported dataframes - Appointments dataframe
    """


    ## Function to clean ASUNTO column
    """
    Function to clean ASUNTO column
    """
    def Asunto_synth(row):

        res = 0


        ## Searching for speciality based on doctor
        if row['NOMBRE DEL CLÍNICO'] in meds_dict_ref:
            if len(meds_dict_ref[row['NOMBRE DEL CLÍNICO']]['Especialidad']) == 1:
                res = meds_dict_ref[row['NOMBRE DEL CLÍNICO']]['Especialidad'][0]
                return res

        ## Searching for speciality based on related keywords if doctor based search was not successful
        if res == 0:
            for sp in specialties_ref:
                for sp_t in specialties_ref[sp]:
                    if sp_t in row['ASUNTO']:
                        res = sp
                        return res

        if res == 0:
            res = 'OTROS'
            # res = row

        return res


    ## Eliminating non relevant columns
    nrc = [col for col in dfa.columns if col not in rca]
    dfa.drop(nrc, axis=1, inplace=True)


    ## Parsing date
    dfa.loc[:, 'FECHA'] = pd.to_datetime(dfa['FECHA'], format='%Y-%m-%d')


    ## Cleaning entries in columns ASUNTO and NOMBRE DEL CLÍNICO
    c_cols = ['ASUNTO', 'NOMBRE DEL CLÍNICO']
    dfa.loc[:, c_cols] = dfa.loc[:, c_cols].fillna('NO_INFO')
    for col in c_cols:

        dfa.loc[:, col] = dfa[col].str.upper().str.strip()

        ccf = [
            lambda x: re.sub('Á', 'A', x),
            lambda x: re.sub('É', 'E', x),
            lambda x: re.sub('Í', 'I', x),
            lambda x: re.sub('Ó', 'O', x),
            lambda x: re.sub('Ú', 'U', x),
        ]

        for fun in ccf:
            dfa.loc[:, col] = dfa[col].apply(fun)


    ## Clean ASUNTO column
    dfa.loc[:, 'ASUNTO_sinth'] = dfa.apply(Asunto_synth, axis=1)


    ## Eliminating entries with appointment status different from "Completada"
    m1 = dfa['ESTADO DE LA CITA'] == 'Completada'
    dfa = dfa.loc[m1, :]


    ## Adding index column
    dfa.insert(0, '#', range(1, dfa.shape[0] + 1))


    ## Adding week number as string
    dfa.loc[:, 'Week_num'] = dfa['FECHA'].apply(add_week_num)


    return dfa





'------------------------------------------------------------------------------------------'
###############################################
## Data analysis - Appointments - Analysis 1 ##
###############################################


## Creating dataframe with sum of appoitments per week per speciality
def data_processing_appointments_A1(dfa, loc='ALL'):
    """
    Creating dataframe with sum of appoitments per week per speciality
    """


    ## Eliminating from analysis specialities that account for a participation smaller that the set treshold
    def selecting_sps_over_treshold(dfax):

        dfx = dfax.copy()

        dfx.loc['Sum', :] = dfx.sum()

        all_sum = dfx.loc['Sum', :].sum()

        dfx.loc['Part_sum', :] = dfx.loc['Sum', :]/all_sum

        rc_sps = [col for col in dfx.columns if dfx.loc['Part_sum', col] > sp_tsh]

        return rc_sps


    dfax = dfa.copy()


    ## Homologating locations' names
    dfax['Loc_Hom'] = dfax['SITIO'].apply(homologate_locations)


    ## Filtering to a specific location according to function's parameters
    if loc in locations_ref:
        m1 = dfax['Loc_Hom'] == loc
        dfax = dfax.loc[m1, :]
    elif loc != 'ALL':
        raise ValueError('The site specified in the parameters is not valid')


    ## Leaving only relevant columns
    rc = [
        '#',
        'Week_num',
        'ASUNTO_sinth'
    ]
    dfax.drop([nrc for nrc in dfax.columns if nrc not in rc], axis=1, inplace=True)


    ## Counting appointments and filling Null values
    dfax = dfax.groupby(['Week_num', 'ASUNTO_sinth']).count().unstack().fillna(0)
    dfax.columns = dfax.columns.droplevel()


    ## Eliminating from analysis specialities that account for a participation smaller that the set treshold
    rc_sps = selecting_sps_over_treshold(dfax)
    dfax.drop([nrc for nrc in dfax.columns if nrc not in rc_sps], axis=1, inplace=True)


    return dfax



## Display bar graph with count of all confirmed appointments per week per speciality
def graph_appointments_A1(dfax, loc='ALL'):

    ## x-axis
    x_axis = list(dfax.index.unique())

    ## Bars
    sps = dfax.columns

    ## Create and display graph
    fig = go.Figure(data=[go.Bar(name=sp, x=x_axis, y=dfax[sp]) for sp in sps])

    fig.update_layout(
        title = 'Conteo de citas confirmadas por especialidad - ({})'.format(loc),
        xaxis_title = 'Semana',
        yaxis_title = 'Número de citas',
        barmode='group',
        autosize=False,
        width=10000,
        height=500
    )
    fig.update_xaxes(type="category")

    fig.show()





'------------------------------------------------------------------------------------------'
###############################################
## Data analysis - Appointments - Analysis 2 ##
###############################################


## Counting number of confirmed appointments and percent change
def data_processing_appointments_A2(dfa, loc='ALL'):
    """
    Counting number of confirmed appointments and percent change
    """

    dfax = dfa.copy()


    ## Homologating locations' names
    dfax['Loc_Hom'] = dfax['SITIO'].apply(homologate_locations)


    ## Filtering to a specific location according to function's parameters
    if loc in locations_ref:
        m1 = dfax['Loc_Hom'] == loc
        dfax = dfax.loc[m1, :]
    elif loc != 'ALL':
        raise ValueError('The site specified in the parameters is not valid')


    rc = [
        'ASUNTO_sinth',
        '#',
        'FECHA'
    ]
    dfax.drop([nrc for nrc in dfax.columns if nrc not in rc], axis=1, inplace=True)
    dfax.set_index('FECHA', drop=True, inplace=True)

    m1 = dfax.index < datetime(2020, 6, 1)
    dfax = dfax.loc[m1, :]


    dfax = dfax.groupby([dfax.index.year, dfax.index.quarter, 'ASUNTO_sinth']).count().unstack().fillna(0)
    dfax.columns = dfax.columns.droplevel()


    ## Creating percent change columns
    for col in dfax.columns:
        dfax.loc[:, col +'_pc'] = dfax[col].diff()/dfax[col].shift()
        dfax.loc[:, col +'_pc'] = dfax[col +'_pc'].fillna(0)
        dfax.loc[:, col +'_pc'] = dfax[col +'_pc'].replace([np.inf, -np.inf], 0)


    ## Adding date as string
    dfax['Date_str'] = dfax.index.get_level_values(0).astype(str) + ' - Q' + dfax.index.get_level_values(1).astype(str)


    return dfax



## Appointments analysis 2 graph
def graph_appointments_A2(dfax, loc='ALL'):
    """
    Appointments analysis 2 graph
    """


    ## Creating structure of nested lists with secondary axis statements
    def sec_ax_statement_structure(graphs, cols):
        """
        Creating structure of nested lists with secondary axis statements
        """
        rl=[]
        ary=[]
        sec_ax_statement = {"secondary_y": True}

        for r in range(0, rows):
            for c in range(0, cols):
                rl.append(sec_ax_statement)

            ary.append(rl)
            rl=[]

        return ary



    graphs = [col for col in dfax.columns if ('_pc' not in col) and ('_str' not in col)]

    rows = math.ceil((len(graphs))/2)
    cols = 2

    fig = make_subplots(rows=rows, cols=cols,
                        subplot_titles=tuple(graphs),
                        specs=sec_ax_statement_structure(graphs, cols)
                       )

    i = 1
    j = 1
    for graph in graphs:

        fig.add_trace(
            go.Bar(
                x=dfax['Date_str'],
                y=dfax[graph],
                name='{} - Consultas confirmadas'.format(graph)
            ),
            secondary_y=False,
            row=j, col=i
        )

        fig.add_trace(
            go.Scatter(
                x=dfax['Date_str'],
                y=dfax[graph + '_pc'],
                name='{} - Cambio porcentual'.format(graph)
            ),
            secondary_y=True,
            row=j, col=i
        )

        i += 1
        if i == 3:
            i = 1
            j += 1

    fig.update_layout(
        title = 'Número de consultas confirmadas y cambio porcentual - {}'.format(loc),
        autosize=False,
        width=1600,
        height=2000
    )


    fig.show()





'------------------------------------------------------------------------------------------'
##############################################
## Data analysis - Sales - Cleaning main df ##
##############################################


## Cleaning imported dataset
def dfs_clean(dfs):
    """
    Cleaning imported dataset
    """


    ## Eliminating non relevant columns
    dfs.drop([nrc for nrc in dfs.columns if nrc not in rcs], axis=1, inplace=True)


    ## Eliminating invalid invalid tickets if selected
    m1 = dfs['State'] != 'Inválida'
    dfs = dfs.loc[m1, :]
    dfs.drop(['State'], axis=1, inplace=True)


    ## Parsing date column
    dfs.loc[:, 'BillDate'] = pd.to_datetime(dfs['BillDate'], format='%Y-%m-%dT%H:%M:%S.%f')


    ## Cleaning selected columns
    c_cols = ['Provider', 'BilledBy', 'DescriptionES']
    dfs.loc[:, c_cols] = dfs.loc[:, c_cols].fillna('NO_INFO')
    for col in c_cols:

        dfs.loc[:, col] = dfs[col].str.upper().str.strip()

        ccf = [
            lambda x: re.sub('Á', 'A', x),
            lambda x: re.sub('É', 'E', x),
            lambda x: re.sub('Í', 'I', x),
            lambda x: re.sub('Ó', 'O', x),
            lambda x: re.sub('Ú', 'U', x),
        ]

        for fun in ccf:
            dfs.loc[:, col] = dfs[col].apply(fun)


    ## Adding index column
    dfs.insert(0, '#', range(1, dfs.shape[0] + 1))


    ## Adding week number as string
    dfs.loc[:, 'Week_num'] = dfs['BillDate'].apply(add_week_num)


    return dfs





'------------------------------------------------------------------------------------------'
########################################
## Data analysis - Sales - Analysis 1 ##
########################################


##
def data_processing_sales_A1(dfs):
    """
    """


    ## Copy of main dataframe
    dfsx = dfs.copy()


    ## Eliminating non relevant columns for the analysis
    rc = [
        'SiteInfo',
        'Week_num',
        'Total'
    ]
    dfsx.drop([nrc for nrc in dfsx.columns if nrc not in rc], axis=1, inplace=True)
    dfsx.set_index('Week_num', drop=True, inplace=True)


    ## Group results
    dfsx = dfsx.groupby([dfsx.index, dfsx['SiteInfo']]).sum().unstack().fillna(0)
    dfsx.columns = dfsx.columns.droplevel()


    return dfsx



## Creating and displaying figure related to analysis 1
def graph_sales_A1(dfsx):

    fig = go.Figure()

    for col in dfsx.columns:
        fig.add_trace(
            go.Bar(
                x = dfsx.index,
                y = dfsx[col],
                name = col,
                text = dfsx[col].astype('str'),
                textposition = 'inside',
                texttemplate = '$%{value:,.1f}'
            )
        )

    fig.update_layout(
        title = 'Ingresos por sucursal (separando laboratorio)',
        xaxis_title = 'Semana',
        yaxis_title = 'Ingresos [$MXN]',
        barmode='stack',
        autosize=False,
        width=8000,
        height=1000
    )
    fig.update_xaxes(type="category")

    fig.show()





'------------------------------------------------------------------------------------------'
########################################
## Data analysis - Sales - Analysis 2 ##
########################################


##
def data_processing_sales_A2(dfs):
    """
    """


    ## Copy of main dataframe
    dfsx = dfs.copy()


    ## Homologate all locations
    dfsx['Loc_Hom'] = dfsx['SiteInfo'].apply(homologate_locations)


    ## Eliminating non relevant columns for the analysis
    rc = [
        'Loc_Hom',
        'Week_num',
        'Total'
    ]
    dfsx.drop([nrc for nrc in dfsx.columns if nrc not in rc], axis=1, inplace=True)
    dfsx.set_index('Week_num', drop=True, inplace=True)


    ## Group results
    dfsx = dfsx.groupby([dfsx.index, dfsx['Loc_Hom']]).sum().unstack().fillna(0)
    dfsx.columns = dfsx.columns.droplevel()


    return dfsx



## Creating and displaying figure related to analysis 1
def graph_sales_A2(dfsx):

    fig = go.Figure()

    for col in dfsx.columns:
        fig.add_trace(
            go.Bar(
                x = dfsx.index,
                y = dfsx[col],
                name = col,
                text = dfsx[col].astype('str'),
                textposition = 'inside',
                texttemplate = '$%{value:,.1f}'
            )
        )

    fig.update_layout(
        title = 'Ingresos por sucursal (juntando laboratorio)',
        xaxis_title = 'Semana',
        yaxis_title = 'Ingresos [$MXN]',
        barmode='stack',
        autosize=False,
        width=8000,
        height=1000
    )
    fig.update_xaxes(type="category")

    fig.show()





'------------------------------------------------------------------------------------------'
########################################
## Data analysis - Sales - Analysis 3 ##
########################################


##
def data_processing_sales_A3(dfs):
    """
    """


    ## Copy of main dataframe
    dfsx = dfs.copy()


    ## Homologate all locations
    dfsx['Loc_Hom'] = dfsx['SiteInfo'].apply(homologate_locations)


    ## Eliminating non relevant columns for the analysis
    rc = [
        'Loc_Hom',
        'Week_num',
        'Total'
    ]
    dfsx.drop([nrc for nrc in dfsx.columns if nrc not in rc], axis=1, inplace=True)
    dfsx.set_index('Week_num', drop=True, inplace=True)


    ## Group results
    dfsx = dfsx.groupby([dfsx.index, dfsx['Loc_Hom']]).sum().unstack().fillna(0)
    dfsx.columns = dfsx.columns.droplevel()


    ## Creating percent change columns
    for col in dfsx.columns:
        dfsx.loc[:, col +'_pc'] = dfsx[col].diff()/dfsx[col].shift()*100
        dfsx.loc[:, col +'_pc'] = dfsx[col +'_pc'].fillna(0)
        dfsx.loc[:, col +'_pc'] = dfsx[col +'_pc'].replace([np.inf, -np.inf], 0)


    return dfsx



## Appointments analysis 2 graph
def graph_sales_A3(dfsx):
    """
    Sales analysis 3 graph
    """


    ## Creating structure of nested lists with secondary axis statements
    def sec_ax_statement_structure(graphs, cols):
        """
        Creating structure of nested lists with secondary axis statements
        """
        rl=[]
        ary=[]
        sec_ax_statement = {"secondary_y": True}

        for r in range(0, rows):
            for c in range(0, cols):
                rl.append(sec_ax_statement)

            ary.append(rl)
            rl=[]

        return ary



    graphs = [col for col in dfsx.columns if ('_pc' not in col) and ('_str' not in col)]

    rows = len(graphs)
    cols = 1

    fig = make_subplots(rows=rows, cols=cols,
                        subplot_titles=tuple(graphs),
                        specs=sec_ax_statement_structure(graphs, cols)
                       )

    i = 1
    j = 1
    for graph in graphs:

        fig.add_trace(
            go.Bar(
                x=dfsx.index,
                y=dfsx[graph]
            ),
            secondary_y=False,
            row=j, col=i
        )

        fig.add_trace(
            go.Scatter(
                x=dfsx.index,
                y=dfsx[graph + '_pc']
            ),
            secondary_y=True,
            row=j, col=i
        )

        i += 1
        if i == cols + 1:
            i = 1
            j += 1

    fig.update_layout(
        title = 'Ventas de cada ubicación',
        autosize=False,
        width=2000,
        height=2000
    )

    fig.update_xaxes(type="category")


    fig.show()
