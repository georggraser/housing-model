"""

@author: guuug
"""

# IMPORTS

import inputs
import os
# import pandas as pd

# GLOBALS

# Distribution of demolition and restoration rates
# depending on the year of construction
# TODO: genauer raussuchen: own estimations based on bbsr
DISTRIBUTION_BUILDINGS = os.path.join(
                                'data', 'distribution_buildings.xlsx')

# demographic developement of germany based on different
# population models
# source: https://www-genesis.destatis.de \
# /genesis//online?operation=table&code=12421-0001& \
# bypass=true&levelindex=0&levelid=1643115777925#abreadcrumb
DEMOGRAPHIC_DEVELOPEMENT = os.path.join(
                                'data', '12421-0001.xlsx')

# Building typology data from IWU (Institut Wohnen und Umwelt),
# https://www.iwu.de/fileadmin/tools/tabula/TABULA-Analyses_DE-Typology_DataTables.zip
TABULA = os.path.join(
    'data', 'TABULA-Analyses_DE-Typology_ResultData.xlsx')

# Weighting of the building typology in 2019 based on a weighted building
# typology from 2011 [1] and supplemented by energetic modernisation [2] and
# new buildings [3] and demolition [3, 4]
# [1] https://www.iwu.de/fileadmin/user_upload/dateien/energie/klima_altbau/ \
# Fl%C3%A4chen_Geb%C3%A4udetypologie_Okt_2013.pdf
# [2] https://www.iwu.de/fileadmin/publikationen/gebaeudebestand/ \
# 2018_IWU_CischinskyEtDiefenbach_Datenerhebung-Wohngeb%C3%A4udebestand-2016.pdf
# [3] TODO: genauer raussuchen: www.destatis.de
# [4] TODO: genauer raussuchen bbsr
SHARE_BUILDINGS_2019 = os.path.join(
    'data', 'share_buildings_2019.xlsx')

# Input data - different scenarios
SCENARIOS = os.path.join('input', 'parameter_scenarios.xlsx')

# Hyperparameter
HYPERPARAMETER = os.path.join('input', 'hyperparameter.xlsx')

# METHODS


def translate(k):
    pass


def housing_model(df_tabula, df_share_buildings, dist_buildings, params,
                  hyperparameter):
    # take share buildings and connect the data with df_tabula
    # only merge where living space != nan in df_share_buildings
    df_share_buildings = df_share_buildings.loc[
        df_share_buildings['living_space_mio.m2'] > 0]
    df_tab_buildings = df_tabula.merge(df_share_buildings,
                                       left_on='identifier',
                                       right_on='tabula_code')
    # only use the columns we need
    df_tb_keys = ['building_type', 'building_code', 'building_variant',
                  'living_space_mio.m2']
    df_tab_buildings = df_tab_buildings[df_tb_keys]
    # TODO: add in test: check for doublettes in tabula_code
    # start with 2020 until 2060
    # which range(len(params)) doesn't matter -> it reflects the #years
    for i in range(len(params['restoration_rate'])):
        # 001 means not restaurated
        bv = df_tab_buildings['building_variant']
        df_unrest = df_tab_buildings.loc[bv == '001']
        # calculate restoration area
        rest_area_i = params['restoration_rate'][i] \
            * params['total_living_space'][i]
        # restoration_area.append(rest_area_i)
        # calculate restauration area building-class wise
        # EFH_A --> A, MFH_A --> A, ...
        # TODO: add in test: check if building code is in ['A', 'B', ..., 'L']
        bc = [x.split('_')[-1] for x in df_unrest['building_code']]
        rest_area_bc = {x: rest_area_i * dist_buildings.iloc[1][x]
                        for x in list(set(bc))}
        # get percentage - distribution of house-types
        # in the different house classes (z.B. A: MFH-50%, EFH-20%, ...)
        # write total areas in dist ({A: xy_mio_m2, B: xy_mio_m2, ...})
        dist = {x: 0 for x in bc}
        for x in range(len(df_unrest)):
            line = df_unrest.iloc[x]
            a_to_f = bc[x]  # line['building_code'].split('_')[-1]
            dist[a_to_f] += line['living_space_mio.m2']
            # print('{}: {}'.format(a_to_f, dist[a_to_f]))
        share_buildings = {x: 0. for x in list(set(df_unrest['building_code']))}
        share_rest_area = {}
        for x in range(len(df_unrest)):
            line = df_unrest.iloc[x]
            a_to_f = bc[x]  # line['building_code'].split('_')[-1]
            share_buildings[line['building_code']] = \
                line['living_space_mio.m2'] / dist[a_to_f]
            if hyperparameter['restauration_building_type bias'] == 'no':
                lbc = line['building_code']
                share_rest_area[lbc] = share_buildings[lbc] \
                    * rest_area_bc[a_to_f]
                df_tab_buildings.loc[x, 'restauration area {}'.format(2020+i)] = share_rest_area[lbc]
            elif hyperparameter['restauration_building_type bias'] == 'yes':
                print('NOT YET')
                pass
        rest_deep_amb = params['restoration_deep_amb'][i]
        living_space_subt_1 = {}
        living_space_add_2 = {}
        living_space_add_3 = {}
        for x in range(len(df_tab_buildings)):
            line = df_tab_buildings.iloc[x]
            key = line['building_code']
            if line['building_variant'] == '001':
                living_space_subt_1[key] = \
                    line['living_space_mio.m2'] - share_rest_area[key]
                df_tab_buildings.loc[x, 'calc_living_space {}'.format(2020+i)] = \
                    living_space_subt_1[key]
                living_space_add_2[key] = (1 - rest_deep_amb) \
                    * share_rest_area[key]
                living_space_add_3[key] = rest_deep_amb * share_rest_area[key]
            elif line['building_variant'] == '002':
                living_space_add_2[key] += line['living_space_mio.m2']
                df_tab_buildings.loc[x, 'calc_living_space {}'.format(2020+i)] = living_space_add_2[key]
            elif line['building_variant'] == '003':
                living_space_add_3[key] += line['living_space_mio.m2']
                df_tab_buildings.loc[x, 'calc_living_space {}'.format(2020+i)] = living_space_add_3[key]
        print(df_tab_buildings.to_markdown())
        exit(1)


def main():
    # load inputs
    il = inputs.InputLoader()
    hyperparameter = il.load_hyperparameter(HYPERPARAMETER)
    scen_params = il.load_param(SCENARIOS)
    # load data
    dl = inputs.DataLoader()
    df_tabula = dl.load_tabula(TABULA)
    dem_dev = dl.load_demographic_developement(DEMOGRAPHIC_DEVELOPEMENT)
    df_share_buildings, total_living_space_2019 = dl.load_share_buildings(
                                                SHARE_BUILDINGS_2019)
    dist_buildings = dl.load_dist_buildings(DISTRIBUTION_BUILDINGS)

    if 'all' in hyperparameter['scenario']:
        chosen_scenarios = list(scen_params.keys())
    else:
        chosen_scenarios = hyperparameter['scenario']
    # iterate through given scenarios and process them successively
    for scen in chosen_scenarios:
        # calculate rates
        rc = inputs.RateCalculator()
        bev_var = hyperparameter['bev_variant']
        bev = dem_dev[bev_var]
        params = rc.rates(total_living_space_2019, bev, scen_params[scen])
        housing_model(df_tabula, df_share_buildings, dist_buildings, params, hyperparameter)


if __name__ == '__main__':
    '''
    starts the main function when the file is being called
    '''
    main()
