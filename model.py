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


def calc_dist(df_tab_buildings, bc, bv_r_d, current_year, is_r, calc_ls):
    # get percentage - distribution of house-types
    # in the different house classes (z.B. A: MFH-50%, EFH-20%, ...)
    # write total areas in dist ({A: ls_, B: ls_ ...})
    dist = {x: 0 for x in bc}
    # TODO: eliminate need for df_unrest
    for x in range(len(df_tab_buildings)):
        line = df_tab_buildings.iloc[x]
        if line['building_variant'] == bv_r_d:
            a_to_l = line['building_code'].split('_')[-1]
            if is_r:
                ls_mio = line['living_space_{}'.format(
                    current_year-1)]
            else:
                ls_mio = line[calc_ls]
            dist[a_to_l] += ls_mio
    return dist


def calc_r_ic(df_tab_buildings, hyperparameter, dist_buildings,
              r_d_area_i, bv_r_d, current_year, is_r, calc_ls):
    # EFH_A --> A, MFH_A --> A, ...
    # TODO: add in test: check if building code is in ['A', 'B', ..., 'L']
    bc = list(set([x.split('_')[-1]
                   for x in df_tab_buildings['building_code']]))
    dist = calc_dist(df_tab_buildings, bc, bv_r_d, current_year, is_r, calc_ls)

    r_d_ic = {}   # EFH_A: [value, idx]
    for idx in range(len(df_tab_buildings)):
        line = df_tab_buildings.iloc[idx]
        if line['building_variant'] == bv_r_d:
            a_to_l = line['building_code'].split('_')[-1]
            if is_r:
                ls_mio = line['living_space_{}'.format(
                    current_year-1)]
            else:
                ls_mio = line[calc_ls]
            lbc = line['building_code']
            if dist[a_to_l] == 0:
                share_buildings = 0
            else:
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
              current_year, is_r, calc_ls):
    """
    short description
    Params: 
        r_d_ic: dict, {EFH_A: [new_living_space, idx]}

    Returns: 
    """
    r_d_rem_check = False
    for lbc, [v, idx] in r_d_ic.items():
        if is_r:
            ls_mio = df_tab_buildings.at[idx, 'living_space_{}'.format(
                current_year-1)]
        else:
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
                   r_d_area_i, bv_r_d, current_year, calc_ls, is_r):
    # EFH_A: [1, 0] <-- rest space available (1), nothing to redistribute
    # EFH_A: [0, 0.123] <-- rest space full (0), 0.123 to redistribute
    r_d_rem = {}  # restoration remaining
    r_d_final = {}  # EFH_A: (rest, idx) restoration
    r_carryover_002 = 0   # sum of restauration that can't be distributed
    r_d_ic = calc_r_ic(df_tab_buildings, hyperparameter, dist_buildings,
                       r_d_area_i, bv_r_d, current_year, is_r, calc_ls)
    r_d_rem_check, r_d_final, r_d_rem = check_r_d(r_d_ic, r_d_rem, r_d_final,
                                                  df_tab_buildings,
                                                  current_year, is_r, calc_ls)

    # sum of restauration/demolition area
    r_d_sum_ic = sum([x for [x, _] in r_d_final.values()])
    # check for area to be restaurated/demolished. No area left, nothing to do
    if r_d_sum_ic == 0:
        return r_d_final, r_carryover_002
    else:
        r_d_share_initial = {k: [x/r_d_sum_ic, idx] for k, [x, idx]
                             in r_d_final.items()}
        r_d_total_rem = r_d_area_i - sum([k for [k, _] in r_d_final.values()])
        if r_d_total_rem > 0.001:
            r_d_rem_check = True
        while r_d_rem_check:
            r_d_dist_keys = [k for k, [a, _] in r_d_rem.items() if a == 0]
            r_d_share_rem = []  # share of remaining rest/dem area
            for k in r_d_dist_keys:
                if k in r_d_share_initial.keys():
                    r_d_share_rem.append(r_d_share_initial[k][0])

            # don't let it divide by 0
            if sum(r_d_share_rem) > 0.999:
                r_d_rem_check = True
                break

            r_d_dist_factor = 1 / (1 - sum(r_d_share_rem))
            r_d_share_ic = {k: [share * r_d_dist_factor, idx] for
                            k, [share, idx] in r_d_share_initial.items()
                            if k not in r_d_dist_keys}
            r_d_total_rem = r_d_area_i - \
                sum([k for [k, _] in r_d_final.values()])
            add_r_d = {k: [share * r_d_total_rem, idx] for k, [share, idx]
                       in r_d_share_ic.items()}

            # add add_r_d to r_d_final
            r_d_ic = {}
            for k in r_d_final.keys():
                if k in add_r_d.keys():
                    r_d_ic[k] = r_d_final[k]
                    r_d_ic[k][0] += add_r_d[k][0]

            r_d_rem_check, r_d_final, r_d_rem = check_r_d(r_d_ic, r_d_rem,
                                                          r_d_final,
                                                          df_tab_buildings,
                                                          current_year, is_r,
                                                          calc_ls)

            if r_d_total_rem > 0.001:
                r_d_rem_check = True

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
                if is_r:
                    if hyperparameter['second_amb_restauration'] == 'no':
                        r_d_rem_check = True
                    elif hyperparameter['second_amb_restauration'] == 'yes':
                        r_carryover_002 = sum(
                            [v for [_, v] in r_d_rem.values()])
                        print('WARNING - you are leaving well-coded area')
                        r_carryover_002 = 0
                else:
                    # for demolition: let the leftovers where they are
                    r_d_rem_check = True
        return r_d_final, r_carryover_002


def apply_r_d(df_tab_buildings, r_d_col, r_deep_amb,
              current_year, calc_ls, is_r):
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
        for y in df_masked.index:
            line = df_tab_buildings.iloc[y]
            if is_r:
                ls_mio = line['living_space_{}'.format(current_year-1)]
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


def apply_nb(df_tab_buildings, nb_area_i, i, params, current_year, calc_ls):
    nb_sfh_area = params['new_building_share_sfh'][i] * nb_area_i
    nb_th_area = params['new_building_share_th'][i] * nb_area_i
    nb_mfh_area = params['new_building_share_mfh'][i] * nb_area_i
    nb_amb = params['new_building_deep_amb'][i]
    nb_col = 'new_building_area_{}'.format(current_year)

    def set_values(line, bc, area, nb_amb, df_tab_buildings, idx):
        if line['building_code'] == bc and line['building_variant'] == '002':
            df_tab_buildings.loc[idx, nb_col] = area * (1-nb_amb)
        elif line['building_code'] == bc and line['building_variant'] == '003':
            df_tab_buildings.loc[idx, nb_col] = area * nb_amb
        return df_tab_buildings
    for idx in range(len(df_tab_buildings)):
        line = df_tab_buildings.iloc[idx]
        df_tab_buildings.loc[idx, nb_col] = 0
        df_tab_buildings = set_values(
            line, 'EFH_L', nb_sfh_area, nb_amb, df_tab_buildings, idx)
        df_tab_buildings = set_values(
            line, 'MFH_L', nb_th_area, nb_amb, df_tab_buildings, idx)
        df_tab_buildings = set_values(
            line, 'RH_L', nb_mfh_area, nb_amb, df_tab_buildings, idx)

    df_tab_buildings.loc[:, 'living_space_{}'.format(current_year)] = \
        df_tab_buildings[calc_ls] + df_tab_buildings[nb_col]
    return df_tab_buildings


def restauration(params, i, hyperparameter, dist_buildings, bv_r_d,
                 current_year, df_tab_buildings, calc_ls):
    # restoration calculation begins
    r_area_i = params['restoration_rate'][i] \
        * params['total_living_space']['{}'.format(2019 + i)]
    r_final, r_carryover_002 = calc_r_d_final(hyperparameter,
                                              dist_buildings,
                                              df_tab_buildings,
                                              r_area_i, bv_r_d,
                                              current_year, calc_ls,
                                              is_r=True)
    r_col = 'restauration_area_{}'.format(current_year)
    for (v, idx) in r_final.values():
        df_tab_buildings.loc[idx, r_col] = v

    r_deep_amb = params['restoration_deep_amb'][i]
    df_tab_buildings = apply_r_d(df_tab_buildings, r_col, r_deep_amb,
                                 current_year, calc_ls, is_r=True)

    # TODO: this ain't working alright - repair - dead code ahead
    if r_carryover_002 != 0:
        if hyperparameter['second_amb_restauration'] == 'yes':
            ls_mio = []
            cls = []
            for idx in range(len(df_tab_buildings)):
                line = df_tab_buildings.loc[idx]
                if line['building_variant'] == bv_r_d:
                    ls_mio.append(line['living_space_2019'])
                    cls.append(line['calc_living_space_2020'])
            r_a = sum(ls_mio) - sum(cls) + r_carryover_002
            print(r_carryover_002)
            print(r_a)
            print(r_area_i)
            bv_r = '002'
            r_final, _ = calc_r_d_final(hyperparameter,
                                        dist_buildings,
                                        df_tab_buildings,
                                        r_carryover_002, bv_r,
                                        current_year, calc_ls,
                                        is_r=True)
            for (v, idx) in r_final.values():
                df_tab_buildings.loc[idx, r_col] = v
    return df_tab_buildings


def demolition(params, i, hyperparameter, dist_buildings, bv_r_d,
               current_year, df_tab_buildings, calc_ls):
    # total ls from last year (initially 2019)
    d_area_i = params['demolition_rate'][i] \
        * params['total_living_space']['{}'.format(2019 + i)]
    d_final, _ = calc_r_d_final(hyperparameter,
                                dist_buildings,
                                df_tab_buildings,
                                d_area_i, bv_r_d,
                                current_year, calc_ls,
                                is_r=False)
    d_col = 'demolition_area_{}'.format(current_year)
    for (v, idx) in d_final.values():
        df_tab_buildings.loc[idx, d_col] = v

    df_tab_buildings = apply_r_d(df_tab_buildings, d_col, None,
                                 current_year, calc_ls, is_r=False)
    return df_tab_buildings


def new_buildings(params, i, hyperparameter, dist_buildings, bv_r_d,
                  current_year, df_tab_buildings, calc_ls):
 # total ls from last year (initially 2019)
    nb_area_i = params['new_building_rate'][i] \
        * params['total_living_space']['{}'.format(2019 + i)]
    df_tab_buildings = apply_nb(df_tab_buildings, nb_area_i, i,
                                params, current_year, calc_ls)
    return df_tab_buildings


def housing_model(df_tabula, df_share_buildings, dist_buildings, params,
                  hyperparameter):
    # take share buildings and connect the data with df_tabula
    # only merge where living space != nan in df_share_buildings

    df_share_buildings = df_share_buildings.loc[
        df_share_buildings['living_space_2019'] > 0]
    df_tab_buildings = df_tabula.merge(df_share_buildings,
                                       left_on='identifier',
                                       right_on='tabula_code')
    # only use the columns we need
    df_tb_keys = ['building_type', 'building_code', 'building_variant',
                  'living_space_2019']
    df_tab_buildings = df_tab_buildings[df_tb_keys]
    bv_r_d = '001'  # building_variant_restauration and demolition
    # TODO: add in test: check for doublettes in tabula_code
    # start with 2020 until 2060
    for i in range(len(params['years'])):
        current_year = params['years'][i]
        calc_ls = 'calc_living_space_{}'.format(current_year)
        df_tab_buildings = restauration(params, i, hyperparameter,
                                        dist_buildings, bv_r_d, current_year,
                                        df_tab_buildings, calc_ls)
        df_tab_buildings = demolition(params, i, hyperparameter,
                                      dist_buildings, bv_r_d,
                                      current_year, df_tab_buildings, calc_ls)
        df_tab_buildings = new_buildings(params, i, hyperparameter,
                                         dist_buildings, bv_r_d,
                                         current_year, df_tab_buildings, calc_ls)
        print('processed year {}'.format(current_year))
        # TODO: check if spec_rest_area < wohnfläche - dann so wie bisher
        # else: wenn eine oder nicht alle > wohnfläche: dann umverteilen auf
        # die anderen der unsanierten Gebäude (Gebäudeklassenübergreifend)
        # Umverteilung: Bei welchen ist noch Platz?
        # else: wenn es bei allen nicht klappt: 2 Möglichkeiten
        # a) wir lassens (nicht sanieren)
        # b) das sanierte (in building_variant 002)  wird nochmal saniert
        # (bv 003)
    df_tab_buildings.to_excel(os.path.join(
        'output', 'building_stock_dev.xlsx'))


def main():
    # TODO: Change xlsx to ods everywhere - only use open formats
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
