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


def calc_dist(df_tab_buildings, bc, bv_r_d, current_year, is_r):
    # get percentage - distribution of house-types
    # in the different house classes (z.B. A: MFH-50%, EFH-20%, ...)
    # write total areas in dist ({A: xy_mio_m2, B: xy_mio_m2, ...})
    dist = {x: 0 for x in bc}
    # TODO: eliminate need for df_unrest
    for x in range(len(df_tab_buildings)):
        line = df_tab_buildings.iloc[x]
        if line['building_variant'] == bv_r_d:
            a_to_l = line['building_code'].split('_')[-1]
            if is_r:
                ls_mio = line['living_space_mio.m2_{}'.format(
                    current_year-1)]
            else:
                calc_ls = 'calc_living_space {}'.format(current_year)
                ls_mio = line[calc_ls]
            dist[a_to_l] += ls_mio
    return dist


def calc_r_ic(df_tab_buildings, hyperparameter, dist_buildings,
              r_d_area_i, bv_r_d, current_year, is_r):
    # EFH_A --> A, MFH_A --> A, ...
    # TODO: add in test: check if building code is in ['A', 'B', ..., 'L']
    bc = list(set([x.split('_')[-1]
                   for x in df_tab_buildings['building_code']]))
    dist = calc_dist(df_tab_buildings, bc, bv_r_d, current_year, is_r)

    r_d_ic = {}   # EFH_A: [value, idx]
    for idx in range(len(df_tab_buildings)):
        line = df_tab_buildings.iloc[idx]
        if line['building_variant'] == bv_r_d:
            a_to_l = line['building_code'].split('_')[-1]
            if is_r:
                ls_mio = line['living_space_mio.m2_{}'.format(
                    current_year-1)]
            else:
                calc_ls = 'calc_living_space {}'.format(current_year)
                ls_mio = line[calc_ls]
            lbc = line['building_code']
            share_buildings = ls_mio / dist[a_to_l]
            if hyperparameter['restauration_building_type bias'] == 'no':
                r_d_ic[lbc] = [share_buildings *
                               r_d_area_i *
                               dist_buildings.iloc[1][a_to_l],
                               idx]
            elif hyperparameter['restauration_building_type bias'] == 'yes':
                print('NOT YET')
    return r_d_ic


def check_r_d(r_d_ic, r_d_rem, r_d_final, df_tab_buildings,
              current_year, is_r):
    """
    short description
    Params: 
        r_d_ic: dict, {EFH_A: [new_living_space, idx]}

    Returns: 
    """
    r_d_rem_check = False
    for lbc, [v, idx] in r_d_ic.items():
        if is_r:
            ls_mio = df_tab_buildings.at[idx, 'living_space_mio.m2_{}'.format(
                current_year-1)]
        else:
            calc_ls = 'calc_living_space {}'.format(current_year)
            ls_mio = df_tab_buildings.at[idx, calc_ls]
        if v < ls_mio:
            r_d_final[lbc] = [v, idx]
            r_d_rem[lbc] = [1, 0]
        elif v == ls_mio:
            r_d_final[lbc] = [v, idx]
            r_d_rem[lbc] = [0, 0]  # TODO: check whether this case is needed
        else:
            r_d_final[lbc] = [ls_mio, idx]
            r_d_rem[lbc] = [0, v - ls_mio]
            r_d_rem_check = True
    return r_d_rem_check, r_d_final, r_d_rem


def calc_r_d_final(hyperparameter, dist_buildings, df_tab_buildings,
                   r_d_area_i, bv_r_d, current_year, is_r):
    # EFH_A: [1, 0] <-- rest space available (1), nothing to redistribute
    # EFH_A: [0, 0.123] <-- rest space full (0), 0.123 to redistribute
    r_d_rem = {}  # restoration remaining
    r_d_final = {}  # EFH_A: (rest, idx) restoration
    r_d_carryover_002 = 0   # sum of restauration that can't be distributed
    r_d_ic = calc_r_ic(df_tab_buildings, hyperparameter, dist_buildings,
                       r_d_area_i, bv_r_d, current_year, is_r)
    r_d_rem_check, r_d_final, r_d_rem = check_r_d(
        r_d_ic, r_d_rem, r_d_final, df_tab_buildings, current_year, is_r)
    # sum of restauration area
    r_d_sum_ic = sum([x for [x, _] in r_d_final.values()])
    r_d_share_initial = {k: [x/r_d_sum_ic, idx] for k, [x, idx]
                         in r_d_final.items()}
    while r_d_rem_check:
        r_d_dist_keys = [k for k, [a, _] in r_d_rem.items() if a == 0]
        r_d_share_rem = []  # share of remaining restoration area
        for k in r_d_dist_keys:
            if k in r_d_share_initial.keys():
                r_d_share_rem.append(r_d_share_initial[k][0])

        r_d_dist_factor = 1 / (1 - sum(r_d_share_rem))
        r_d_share_ic = {k: [share * r_d_dist_factor, idx] for k, [share, idx]
                        in r_d_share_initial.items() if k not in r_d_dist_keys}

        r_d_rem_zero = [b for k, [a, b] in r_d_rem.items()
                        if a == 0 and k in r_d_share_initial.keys()]
        add_r_d = {k: [share * sum(r_d_rem_zero), idx] for k, [share, idx]
                   in r_d_share_ic.items()}

        # add add_r_d to r_d_final
        r_d_ic = {}
        for k in r_d_final.keys():
            if k in add_r_d.keys():
                r_d_ic[k] = r_d_final[k]
                r_d_ic[k][0] += add_r_d[k][0]

        r_d_rem_check, r_d_final, r_d_rem = check_r_d(
            r_d_ic, r_d_rem, r_d_final, df_tab_buildings, current_year, is_r)

        r_d_share_initial = r_d_share_ic
        # check for space in restauration area
        # if no space left is true, all
        no_ls_001_check = True
        for k, [v, _] in r_d_rem.items():
            if v == 1 and r_d_final[k][0] != 0.:
                no_ls_001_check = False
                break
        # TODO: repair and implement.
        if no_ls_001_check:
            r_d_carryover_002 = sum([v for [_, v] in r_d_rem.values()])
            print('WARNING - you are leaving well-coded area')
            r_d_carryover_002 = 0
    return r_d_final, r_d_carryover_002


def apply_r_d(df_tab_buildings, r_d_col, r_deep_amb,
              current_year, is_r):
    bc_all = list(set(df_tab_buildings['building_code']))
    # iterate through all building codes and apply the restauration
    for x in bc_all:
        ls_sub_1 = 0
        ls_add_2 = 0
        ls_add_3 = 0
        # only take the indizes of the masked dataframe and use them
        # for the df_tab_buildings to know where the line is
        mask = df_tab_buildings['building_code'] == x
        df_masked = df_tab_buildings[mask]
        calc_ls = 'calc_living_space {}'.format(current_year)
        for y in df_masked.index:
            line = df_tab_buildings.iloc[y]
            if is_r:
                ls_mio = line['living_space_mio.m2_{}'.format(current_year-1)]
            else:
                ls_mio = line[calc_ls]
            if line['building_variant'] == '001':
                ls_sub_1 = ls_mio - line[r_d_col]
                df_tab_buildings.loc[y, calc_ls] = ls_sub_1
                if is_r:
                    ls_add_2 = (1 - r_deep_amb) * line[r_d_col]
                    ls_add_3 = r_deep_amb * line[r_d_col]
            elif line['building_variant'] == '002' and is_r:
                ls_add_2 += ls_mio
                df_tab_buildings.loc[y, calc_ls] = ls_add_2
            elif line['building_variant'] == '003' and is_r:
                ls_add_3 += ls_mio
                df_tab_buildings.loc[y, calc_ls] = ls_add_3
    return df_tab_buildings


def housing_model(df_tabula, df_share_buildings, dist_buildings, params,
                  hyperparameter):
    # take share buildings and connect the data with df_tabula
    # only merge where living space != nan in df_share_buildings

    df_share_buildings = df_share_buildings.loc[
        df_share_buildings['living_space_mio.m2_2019'] > 0]
    df_tab_buildings = df_tabula.merge(df_share_buildings,
                                       left_on='identifier',
                                       right_on='tabula_code')
    # only use the columns we need
    df_tb_keys = ['building_type', 'building_code', 'building_variant',
                  'living_space_mio.m2_2019']
    df_tab_buildings = df_tab_buildings[df_tb_keys]
    bv_r_d = '001'  # building_variant_restauration and demolition
    # TODO: add in test: check for doublettes in tabula_code
    # start with 2020 until 2060
    for i in range(len(params['years'])):
        current_year = params['years'][i]

        # restoration calculation begins
        r_area_i = params['restoration_rate'][i] \
            * params['total_living_space']['{}'.format(2019 + i)]  # total ls from last year (initially 2019)
        r_final, r_carryover_002 = calc_r_d_final(hyperparameter,
                                                  dist_buildings,
                                                  df_tab_buildings,
                                                  r_area_i, bv_r_d,
                                                  current_year,
                                                  is_r=True)
        r_col = 'restauration area {}'.format(current_year)
        for (v, idx) in r_final.values():
            df_tab_buildings.loc[idx, r_col] = v

        r_deep_amb = params['restoration_deep_amb'][i]
        df_tab_buildings = apply_r_d(df_tab_buildings, r_col, r_deep_amb,
                                     current_year, is_r=True)

        # TODO: this ain't working alright - repair - dead code ahead
        if r_carryover_002 != 0:
            if hyperparameter['second_amb_restauration'] == 'yes':
                ls_mio = []
                cls = []
                for idx in range(len(df_tab_buildings)):
                    line = df_tab_buildings.loc[idx]
                    if line['building_variant'] == bv_r_d:
                        ls_mio.append(line['living_space_mio.m2_2019'])
                        cls.append(line['calc_living_space 2020'])
                r_a = sum(ls_mio) - sum(cls) + r_carryover_002
                print(r_carryover_002)
                print(r_a)
                print(r_area_i)
                bv_r = '002'
                r_final, _ = calc_r_d_final(hyperparameter,
                                            dist_buildings,
                                            df_tab_buildings,
                                            r_carryover_002, bv_r,
                                            current_year,
                                            is_r=True)
                for (v, idx) in r_final.values():
                    df_tab_buildings.loc[idx, r_col] = v

        # demolition calculation begins
        d_area_i = params['demolition_rate'][i] \
            * params['total_living_space']['{}'.format(2019 + i)]  # total ls from last year (initially 2019)
        d_final, d_carryover_002 = calc_r_d_final(hyperparameter,
                                                  dist_buildings,
                                                  df_tab_buildings,
                                                  d_area_i, bv_r_d,
                                                  current_year,
                                                  is_r=False)
        d_col = 'demolition area {}'.format(current_year)
        for (v, idx) in d_final.values():
            df_tab_buildings.loc[idx, d_col] = v

        df_tab_buildings = apply_r_d(df_tab_buildings, d_col, None,
                                     current_year, is_r=False)
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
