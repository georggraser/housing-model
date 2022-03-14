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


def calc_dist(df_tab_buildings, bc):
    # get percentage - distribution of house-types
    # in the different house classes (z.B. A: MFH-50%, EFH-20%, ...)
    # write total areas in dist ({A: xy_mio_m2, B: xy_mio_m2, ...})
    dist = {x: 0 for x in bc}
    # TODO: eliminate need for df_unrest
    for x in range(len(df_tab_buildings)):
        line = df_tab_buildings.iloc[x]
        if line['building_variant'] == '001':
            a_to_l = line['building_code'].split('_')[-1]
            dist[a_to_l] += line['living_space_mio.m2']
    return dist


def check_restauration(share_rest_area_tmp, rest_space, share_rest_area,
                       df_tab_buildings):
    redistribute_space = False
    for lbc, [v, idx] in share_rest_area_tmp.items():
        ls_mio = df_tab_buildings.at[idx, 'living_space_mio.m2']
        if v < ls_mio:
            share_rest_area[lbc] = [v, idx]
            rest_space[lbc] = [1, 0]
        elif v == ls_mio:
            share_rest_area[lbc] = [v, idx]
            rest_space[lbc] = [0, 0]
        else:
            share_rest_area[lbc] = [ls_mio, idx]
            rest_space[lbc] = [0, v - ls_mio]
            redistribute_space = True
    return redistribute_space, share_rest_area, rest_space


def restauration(share_rest_area_tmp, df_tab_buildings):
    # EFH_A: [1, 0] <-- rest space available (1), nothing to redistribute
    # EFH_A: [0, 0.123] <-- rest space full (0), 0.123 to redistribute
    rest_space = {}
    share_rest_area = {}  # <-- EFH_A: (rest, idx)
    redistribute_space, share_rest_area, rest_space = check_restauration(
        share_rest_area_tmp, rest_space, share_rest_area, df_tab_buildings)
    while redistribute_space:
        # sum of restauration area
        no_space_left = True
        for [v, _] in rest_space.values():
            if v == 1:
                no_space_left = False
        if no_space_left:
            print('no space left for restauration....')
            print(rest_space)
            print(share_rest_area)
            exit(1)
        rest_sum = sum([x for [x, _] in share_rest_area.values()])
        rest_dist_raw = {k: [x/rest_sum, idx] for k, [x, idx]
                         in share_rest_area.items()}
        dist_space_keys = [k for k, [a, _] in rest_space.items() if a == 0]
        dist_space_values = []
        for k in dist_space_keys:
            dist_space_values.append(rest_dist_raw[k][0])
        dist_space_sum = sum(dist_space_values)
        rest_dist_factor = 1 / (1 - dist_space_sum)
        rest_dist = {k: [rdr * rest_dist_factor, idx] for k, [rdr, idx]
                     in rest_dist_raw.items() if k not in dist_space_keys}

        space_values = [b for [a, b] in rest_space.values() if a == 0]
        rest_diff = []
        for b in space_values:
            rest_diff.append(b)
        rest_diff_sum = sum(rest_diff)
        add_rest_area = {k: [rdr * rest_diff_sum, idx] for k, [rdr, idx]
                         in rest_dist.items()}

        # add add_rest_area to share_rest_area
        share_rest_area_tmp = {}
        for k in share_rest_area.keys():
            if k in add_rest_area.keys():
                share_rest_area_tmp[k] = share_rest_area[k]
                share_rest_area_tmp[k][0] += add_rest_area[k][0]

    redistribute_space, share_rest_area, rest_space = check_restauration(
        share_rest_area_tmp, rest_space, share_rest_area, df_tab_buildings)
    return share_rest_area


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
    bc_all = list(set(df_tab_buildings['building_code']))
    # TODO: add in test: check for doublettes in tabula_code
    # start with 2020 until 2060
    # which range(len(params)) doesn't matter -> it reflects the #years
    # TODO: add some kind of years to iterate over
    for i in range(len(params['restoration_rate'])):
        # restoration_area.append(rest_area_i)
        # calculate restauration area building-class wise
        # EFH_A --> A, MFH_A --> A, ...
        # TODO: add in test: check if building code is in ['A', 'B', ..., 'L']
        bc = list(set([x.split('_')[-1]
                  for x in df_tab_buildings['building_code']]))
        dist = calc_dist(df_tab_buildings, bc)

        # 001 means not restaurated
        bv = df_tab_buildings['building_variant']
        df_unrest = df_tab_buildings.loc[bv == '001']
        share_buildings = {x: 0. for x in list(
            set(df_unrest['building_code']))}
        # calculate restoration area
        rest_area_i = params['restoration_rate'][i] \
            * params['total_living_space'][i]
        # EFH_A: [value, idx]
        share_rest_area_tmp = {}
        for idx in range(len(df_tab_buildings)):
            line = df_tab_buildings.iloc[idx]
            if line['building_variant'] == '001':
                a_to_l = line['building_code'].split('_')[-1]
                ls_mio = line['living_space_mio.m2']
                share_buildings[line['building_code']] = ls_mio / dist[a_to_l]
                if hyperparameter['restauration_building_type bias'] == 'no':
                    lbc = line['building_code']
                    share_rest_area_tmp[lbc] = [share_buildings[lbc] *
                                                rest_area_i *
                                                dist_buildings.iloc[1][a_to_l],
                                                idx]
                elif hyperparameter['restauration_building_type bias'] == 'yes':
                    print('NOT YET')
        share_rest_area = restauration(share_rest_area_tmp, df_tab_buildings)
        for (v, idx) in share_rest_area.values():
            df_tab_buildings.loc[idx, 'restauration area {}'.format(
                2020+i)] = v
        rest_deep_amb = params['restoration_deep_amb'][i]
        # iterate through all building codes and apply the restauration
        for x in bc_all:
            ls_sub_1 = 0
            ls_add_2 = 0
            ls_add_3 = 0
            # only take the indizes of the masked dataframe and use them
            # for the df_tab_buildings to know where the line is
            mask = df_tab_buildings['building_code'] == x
            df_masked = df_tab_buildings[mask]
            for y in df_masked.index:
                line = df_tab_buildings.iloc[y]
                key = line['building_code']
                ls_mio = line['living_space_mio.m2']
                if line['building_variant'] == '001':
                    ls_sub_1 = ls_mio - share_rest_area[key][0]
                    ls_add_2 = (1 - rest_deep_amb) * share_rest_area[key][0]
                    ls_add_3 = rest_deep_amb * share_rest_area[key][0]
                    df_tab_buildings.loc[y, 'calc_living_space {}'
                                         .format(2020+i)] = ls_sub_1
                elif line['building_variant'] == '002':
                    ls_add_2 += ls_mio
                    df_tab_buildings.loc[y, 'calc_living_space {}'
                                         .format(2020+i)] = ls_add_2
                elif line['building_variant'] == '003':
                    ls_add_3 += ls_mio
                    df_tab_buildings.loc[y, 'calc_living_space {}'
                                         .format(2020+i)] = ls_add_3
        print(df_tab_buildings.to_markdown())
        exit(1)
        # TODO: check if spec_rest_area < wohnfläche - dann so wie bisher
        # else: wenn eine oder nicht alle > wohnfläche: dann umverteilen auf
        # die anderen der unsanierten Gebäude (Gebäudeklassenübergreifend)
        # Umverteilung: Bei welchen ist noch Platz?
        # else: wenn es bei allen nicht klappt: 2 Möglichkeiten
        # a) wir lassens (nicht sanieren)
        # b) das sanierte (in building_variant 002)  wird nochmal saniert
        # (bv 003)


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
        housing_model(df_tabula, df_share_buildings,
                      dist_buildings, params, hyperparameter)


if __name__ == '__main__':
    '''
    starts the main function when the file is being called
    '''
    main()
