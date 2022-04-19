"""

@author: guuug
"""

# IMPORTS

import inputs
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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


def calc_dist(df_tab_years, bc, bv_r_d, current_year, is_r, calc_ls):
    # get percentage - distribution of house-types
    # in the different house classes (z.B. A: MFH-50%, EFH-20%, ...)
    # write total areas in dist ({A: ls_, B: ls_ ...})
    dist = {x: 0 for x in bc}
    for x in range(len(df_tab_years)):
        line = df_tab_years.iloc[x]
        if line['building_variant'] == bv_r_d:
            a_to_l = line['building_code'].split('_')[-1]
            if is_r:
                ls_mio = line['living_space_{}'.format(
                    current_year-1)]
            else:
                ls_mio = line[calc_ls]
            dist[a_to_l] += ls_mio
    return dist


def calc_r_ic(df_tab_years, hyperparameter, dist_buildings,
              r_d_area_i, bv_r_d, current_year, is_r, calc_ls):
    # EFH_A --> A, MFH_A --> A, ...
    # TODO: add in test: check if building code is in ['A', 'B', ..., 'L']
    bc = list(set([x.split('_')[-1]
                   for x in df_tab_years['building_code']]))
    dist = calc_dist(df_tab_years, bc, bv_r_d, current_year, is_r, calc_ls)

    r_d_ic = {}   # EFH_A: [value, idx]
    for idx in range(len(df_tab_years)):
        line = df_tab_years.iloc[idx]
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


def check_r_d(r_d_ic, r_d_rem, r_d_final, df_tab_years,
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
            ls_mio = df_tab_years.at[idx, 'living_space_{}'.format(
                current_year-1)]
        else:
            ls_mio = df_tab_years.at[idx, calc_ls]
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


def calc_r_d_final(hyperparameter, dist_buildings, df_tab_years,
                   r_d_area_i, bv_r_d, current_year, calc_ls, is_r):
    # EFH_A: [1, 0] <-- rest space available (1), nothing to redistribute
    # EFH_A: [0, 0.123] <-- rest space full (0), 0.123 to redistribute
    r_d_rem = {}  # restoration remaining
    r_d_final = {}  # EFH_A: (rest, idx) restoration
    r_carryover_002 = 0   # sum of restauration that can't be distributed
    r_d_ic = calc_r_ic(df_tab_years, hyperparameter, dist_buildings,
                       r_d_area_i, bv_r_d, current_year, is_r, calc_ls)
    r_d_rem_check, r_d_final, r_d_rem = check_r_d(r_d_ic, r_d_rem, r_d_final,
                                                  df_tab_years,
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
                                                          df_tab_years,
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


def apply_r_d(df_tab_years, r_d_col, r_deep_amb,
              current_year, calc_ls, is_r):
    bc_all = list(set(df_tab_years['building_code']))
    # iterate through all building codes and apply the restauration
    for x in bc_all:
        ls_sub_1 = 0
        ls_add_2 = 0
        ls_add_3 = 0
        # only take the indizes of the masked dataframe and use them
        # for the df_tab_years to know where the line is
        mask = df_tab_years['building_code'] == x
        df_masked = df_tab_years[mask]
        for y in df_masked.index:
            line = df_tab_years.iloc[y]
            if is_r:
                ls_mio = line['living_space_{}'.format(current_year-1)]
            else:
                ls_mio = line[calc_ls]
            if line['building_variant'] == '001':
                ls_sub_1 = ls_mio - line[r_d_col]
                df_tab_years.loc[y, calc_ls] = ls_sub_1
                if is_r:
                    ls_add_2 = (1 - r_deep_amb) * line[r_d_col]
                    ls_add_3 = r_deep_amb * line[r_d_col]
            elif line['building_variant'] == '002' and is_r:
                ls_add_2 += ls_mio
                df_tab_years.loc[y, calc_ls] = ls_add_2
            elif line['building_variant'] == '003' and is_r:
                ls_add_3 += ls_mio
                df_tab_years.loc[y, calc_ls] = ls_add_3
    return df_tab_years


def restauration(params, i, hyperparameter, dist_buildings, bv_r_d,
                 current_year, df_tab_years, calc_ls):
    # restoration calculation begins
    r_area_i = params['restoration_rate'][i] \
        * params['total_living_space']['{}'.format(2019 + i)]
    r_final, r_carryover_002 = calc_r_d_final(hyperparameter,
                                              dist_buildings,
                                              df_tab_years,
                                              r_area_i, bv_r_d,
                                              current_year, calc_ls,
                                              is_r=True)
    r_col = 'restauration_area_{}'.format(current_year)
    for (v, idx) in r_final.values():
        df_tab_years.loc[idx, r_col] = v

    r_deep_amb = params['restoration_deep_amb'][i]
    df_tab_years = apply_r_d(df_tab_years, r_col, r_deep_amb,
                             current_year, calc_ls, is_r=True)

    # TODO: this ain't working alright - repair - dead code ahead
    if r_carryover_002 != 0:
        if hyperparameter['second_amb_restauration'] == 'yes':
            ls_mio = []
            cls = []
            for idx in range(len(df_tab_years)):
                line = df_tab_years.loc[idx]
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
                                        df_tab_years,
                                        r_carryover_002, bv_r,
                                        current_year, calc_ls,
                                        is_r=True)
            for (v, idx) in r_final.values():
                df_tab_years.loc[idx, r_col] = v
    return df_tab_years


def demolition(params, i, hyperparameter, dist_buildings, bv_r_d,
               current_year, df_tab_years, calc_ls, d_col):
    # total ls from last year (initially 2019)
    d_area_i = params['demolition_rate'][i] \
        * params['total_living_space']['{}'.format(2019 + i)]
    d_final, _ = calc_r_d_final(hyperparameter,
                                dist_buildings,
                                df_tab_years,
                                d_area_i, bv_r_d,
                                current_year, calc_ls,
                                is_r=False)

    for (v, idx) in d_final.values():
        df_tab_years.loc[idx, d_col] = v

    df_tab_years = apply_r_d(df_tab_years, d_col, None,
                             current_year, calc_ls, is_r=False)
    return df_tab_years


def new_buildings(params, i, df_tab_years, calc_ls, new_ls, nb_col):
    # total ls from last year (initially 2019)
    nb_area_i = params['new_building_rate'][i] \
        * params['total_living_space']['{}'.format(2019 + i)]
    nb_sfh_area = params['new_building_share_sfh'][i] * nb_area_i
    nb_th_area = params['new_building_share_th'][i] * nb_area_i
    nb_mfh_area = params['new_building_share_mfh'][i] * nb_area_i
    nb_amb = params['new_building_deep_amb'][i]

    df_col = pd.DataFrame({nb_col: [0 for _ in range(len(df_tab_years))]})
    bcs = ['EFH_L', 'MFH_L', 'RH_L']
    areas = [nb_sfh_area, nb_mfh_area, nb_th_area]
    for bc, area in zip(bcs, areas):
        bc_map = df_tab_years['building_code'] == bc
        bv_002 = df_tab_years['building_variant'] == '002'
        bv_003 = df_tab_years['building_variant'] == '003'

        nb_L_map_002 = bc_map & bv_002
        df_col[nb_col].loc[nb_L_map_002] = area * (1-nb_amb)

        nb_L_map_003 = bc_map & bv_003
        df_col[nb_col].loc[nb_L_map_003] = area * nb_amb
    df_tab_years.loc[:, nb_col] = df_col
    df_tab_years.loc[:, new_ls] = df_tab_years[calc_ls] + df_tab_years[nb_col]
    return df_tab_years


def heating_demand(df_tab_years, df_heat_demand, space_heat_need,
                   hot_water_need, new_ls, current_year, d_col):
    high_map = df_tab_years['space_heat_need'] >= 120
    middle_map = (df_tab_years['space_heat_need'] >= 90) &\
        (df_tab_years['space_heat_need'] < 120)
    low_map = df_tab_years['space_heat_need'] < 90

    def get_sh_need(map):
        return df_tab_years['space_heat_need'].loc[map] *\
            df_tab_years[new_ls].loc[map]
    high_sh_need = get_sh_need(high_map)
    middle_sh_need = get_sh_need(middle_map)
    low_sh_need = get_sh_need(low_map)
    df_tab_years.loc[:, space_heat_need] = df_tab_years['space_heat_need'] *\
        df_tab_years[new_ls]
    df_tab_years.loc[:, hot_water_need] = df_tab_years['hot_water_need'] *\
        df_tab_years[new_ls]

    # total sum
    df_heat_demand.loc[current_year, 'total_ls'] = sum(
        df_tab_years[new_ls])
    df_heat_demand.loc[current_year, 'total_sh_need'] = sum(
        df_tab_years[space_heat_need])
    df_heat_demand.loc[current_year, 'spec_sh_need'] = \
        df_heat_demand.loc[current_year, 'total_sh_need'] / \
        df_heat_demand.loc[current_year, 'total_ls']
    df_heat_demand.loc[current_year, 'total_hot_water_need'] = sum(
        df_tab_years[hot_water_need])
    df_heat_demand.loc[current_year, 'total_heat_need'] = \
        df_heat_demand.loc[current_year, 'total_sh_need'] + \
        df_heat_demand.loc[current_year, 'total_hot_water_need']
    # sum (>=120)
    df_heat_demand.loc[current_year, 'high_sh_need'] = sum(high_sh_need)
    # sum (<120 >=90)
    df_heat_demand.loc[current_year, 'middle_sh_need'] = sum(middle_sh_need)
    # sum (<90)
    df_heat_demand.loc[current_year, 'low_sh_need'] = sum(low_sh_need)

    # new buildings sh need
    all_inserts_rows = []
    all_inserts_cols = []
    for ch in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']:
        building_list = [f'EFH_{ch}', f'MFH_{ch}', f'RH_{ch}', f'GMH_{ch}']
        for bc in building_list:
            spec_sh_need_all = []
            for bv in ['001', '002', '003']:
                spec_map = (df_tab_years['building_code'] == bc) & \
                    (df_tab_years['building_variant'] == bv)
                spec_sh_need = get_sh_need(spec_map).to_numpy()
                if len(spec_sh_need) == 0:
                    spec_sh_need = np.zeros(1)
                all_inserts_cols.append(f'{bc}_{bv}_sh_need')
                all_inserts_rows.append(spec_sh_need)
                spec_sh_need_all.append(sum(spec_sh_need))
            all_inserts_cols.append(f'{bc}_sh_need')
            all_inserts_rows.append(sum(spec_sh_need_all))
    df_heat_demand.loc[current_year, all_inserts_cols] = all_inserts_rows

    offset = 0
    if current_year > 2019:
        offset = df_heat_demand.loc[current_year-1, 'dem_sh_need_decrease']
        df_heat_demand.loc[current_year, 'dem_sh_need_decrease'] = \
            sum(df_tab_years['space_heat_need'].mul(
                df_tab_years[d_col], fill_value=0)) + offset
    else:
        df_heat_demand.loc[current_year, 'dem_sh_need_decrease'] = 0
    return df_tab_years, df_heat_demand


def plot_heat_demand(df_heat_demand, years):
    high_sh_need = df_heat_demand['high_sh_need']
    middle_sh_need = df_heat_demand['middle_sh_need']
    low_sh_need = df_heat_demand['low_sh_need']

    plt.figure(1)
    # Plot x-labels, y-label and data
    plt.plot([], [], color='blue', label='low_sh_need')
    plt.plot([], [], color='orange', label='middle_sh_need')
    plt.plot([], [], color='brown', label='high_sh_need')

    plt.stackplot(years, low_sh_need, middle_sh_need, high_sh_need,
                  baseline='zero', colors=['blue', 'orange', 'brown'])
    plt.legend()
    plt.title('Heat demand comparison')
    plt.xlabel('years')
    plt.ylabel('space heat need in kwh')
    plt.show()

    # Raumwärme und Warmwasser bedarf
    # total_sh_need = df_heat_demand['total_sh_need']
    total_hot_water_need = df_heat_demand['total_hot_water_need']
    total_heat_need = df_heat_demand['total_heat_need']

    plt.figure(2)
    # Plot x-labels, y-label and data
    # plt.plot([], [], color='blue', label='total_sh_need')
    plt.plot([], [], color='orange', label='total_hot_water_need')
    plt.plot([], [], color='brown', label='total_heat_need')

    plt.stackplot(years, total_hot_water_need, total_heat_need,
                  baseline='zero', colors=['orange', 'brown'])
    plt.legend()
    plt.title('Total heat demand comparison')
    plt.xlabel('years')
    plt.ylabel('space heat need in kwh')
    plt.show()

    # Raumwärmebedarf und spezifischer Wärmebedarf
    total_sh_need = df_heat_demand['total_sh_need']
    spec_sh_need = df_heat_demand['spec_sh_need']

    fig, ax1 = plt.subplots()
    plt.title('Total heat demand comparison')

    color = 'tab:red'
    ax1.set_xlabel('years')
    ax1.set_ylabel('total heat need in TWh', color=color)
    offset = 20000
    limit_ax1 = total_sh_need[0] + offset
    ax1.set_ylim(0, limit_ax1)
    ax1.plot(years, total_sh_need, color=color)
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    limit_ax2 = spec_sh_need[0] / total_sh_need[0] * limit_ax1

    color = 'tab:blue'
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, limit_ax2)
    ax2.plot(years, spec_sh_need, color=color)
    ax2.set_ylabel('specific heat need in kWh/m2', color=color)
    fig.tight_layout()
    plt.legend()
    plt.show()

    #   Wärmebedarf
    plt.figure(3)
    plt.xlabel('years')
    plt.plot([], [], color='purple', label='L+K: 003')
    plt.plot([], [], color='blue', label='L+K: 002')
    plt.plot([], [], color='pink', label='L+K: 001')
    plt.plot([], [], color='red', label='A-J: 003')
    plt.plot([], [], color='orange', label='A-J: 002')
    plt.plot([], [], color='green', label='A-J: 001')
    plt.plot([], [], color='gray', alpha=0.5,  label='demolition')
    to_stack = []
    # for ch in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']:
    for var_idx in ['003', '002', '001']:
        tmp_to_stack = []
        for ch in ['K', 'L']:
            tmp_to_stack.append(df_heat_demand[f'EFH_{ch}_{var_idx}_sh_need'] +
                                df_heat_demand[f'MFH_{ch}_{var_idx}_sh_need'] +
                                df_heat_demand[f'RH_{ch}_{var_idx}_sh_need'] +
                                df_heat_demand[f'GMH_{ch}_{var_idx}_sh_need'])
        to_stack.append(sum(tmp_to_stack))
    for var_idx in ['003', '002', '001']:
        tmp_to_stack = []
        for ch in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']:
            tmp_to_stack.append(df_heat_demand[f'EFH_{ch}_{var_idx}_sh_need'] +
                                df_heat_demand[f'MFH_{ch}_{var_idx}_sh_need'] +
                                df_heat_demand[f'RH_{ch}_{var_idx}_sh_need'] +
                                df_heat_demand[f'GMH_{ch}_{var_idx}_sh_need'])
        to_stack.append(sum(tmp_to_stack))
    to_stack.append(-df_heat_demand['dem_sh_need_decrease'])
    plt.stackplot(years, to_stack, baseline='zero',
                  colors=['purple', 'blue', 'pink', 'red', 'orange', 'green',
                          'gray'])
    plt.legend()

    plt.show()

    # Plot 2: Wärmebedarf nach EFH, RH, MFH und Ab

    # Plot 3: Quadratmeter der unterschiedlichen Gebäude /
    # (müssen wir überlegen wonach wir unterteilen: EFH, RH, MFH und AB?)

    # Plot 4: Plotten wie viel Neubau, Abgang und Bestandsgebäude /
    # (eventuell Bestandsgebäude unterteilt in Buildingvariants)


def housing_model(df_tabula, df_share_buildings, dist_buildings, params,
                  hyperparameter):
    # take share buildings and connect the data with df_tabula
    # only merge where living space != nan in df_share_buildings

    df_share_buildings = df_share_buildings.loc[
        df_share_buildings['living_space_2019'] > 0]
    df_tab_years = df_tabula.merge(df_share_buildings,
                                   left_on='identifier',
                                   right_on='tabula_code')

    bv_r_d = '001'  # building_variant_restauration and demolition
    # TODO: add in test: check for doublettes in tabula_code
    years = params['years'].copy()
    years.insert(0, 2019)
    df_heat_demand = pd.DataFrame(data={}, index=years)
    # DELETE ME FOR DEBUGGING PURPOSES --------------------
    del_me = True
    if del_me:
        df_heat_demand = pd.read_excel(os.path.join(
            'output', 'heat_demand_dev.xlsx'))
        plot_heat_demand(df_heat_demand, years)
        exit(1)
    # ---------------------
    # start with 2020 until 2060
    #all_ls = []
    for i in range(len(params['years'])):
        # TODO: save all unneeded rows to extra table
        current_year = params['years'][i]
        calc_ls = f'calc_living_space_{current_year}'
        new_ls = f'living_space_{current_year}'
        d_col = 'demolition_area_{}'.format(current_year)
        nb_col = f'new_building_area_{current_year}'
        space_heat_need = f'space_heat_need_{current_year}'
        hot_water_need = f'hot_water_need_{current_year}'
        # all_ls.append(new_ls)

        df_tab_years = restauration(params, i, hyperparameter,
                                    dist_buildings, bv_r_d, current_year,
                                    df_tab_years, calc_ls)
        df_tab_years = demolition(params, i, hyperparameter,
                                  dist_buildings, bv_r_d,
                                  current_year, df_tab_years, calc_ls, d_col)
        df_tab_years = new_buildings(params, i, df_tab_years, calc_ls,
                                     new_ls, nb_col)

        # create entries for 2019
        if i == 0:
            sh_need_2019 = 'space_heat_need_2019'
            hw_need_2019 = 'hot_water_need_2019'
            ls_2019 = 'living_space_2019'
            df_tab_years, df_heat_demand = heating_demand(df_tab_years,
                                                          df_heat_demand,
                                                          sh_need_2019,
                                                          hw_need_2019,
                                                          ls_2019,
                                                          current_year-1,
                                                          d_col)
        df_tab_years, df_heat_demand = heating_demand(df_tab_years,
                                                      df_heat_demand,
                                                      space_heat_need,
                                                      hot_water_need,
                                                      new_ls, current_year,
                                                      d_col)
        print(f'processed year {current_year}')

    df_heat_demand.to_excel(os.path.join('output', 'heat_demand_dev.xlsx'))
    #cols = ['space_heat_need'] + all_ls
    #df_tab = df_tab_years[cols]
    #df_tab.to_excel(os.path.join('output', 'luisa_check.xlsx'))
    plot_heat_demand(df_heat_demand, years)
    # TODO: check if spec_rest_area < wohnfläche - dann so wie bisher
    # else: wenn eine oder nicht alle > wohnfläche: dann umverteilen auf
    # die anderen der unsanierten Gebäude (Gebäudeklassenübergreifend)
    # Umverteilung: Bei welchen ist noch Platz?
    # else: wenn es bei allen nicht klappt: 2 Möglichkeiten
    # a) wir lassens (nicht sanieren)
    # b) das sanierte (in building_variant 002)  wird nochmal saniert
    # (bv 003)
    #  df_tab_years.to_excel(os.path.join(
    #    'output', 'building_stock_dev.xlsx'))
    return df_tab_years


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
        df_tab_years = housing_model(df_tabula, df_share_buildings,
                                     dist_buildings, params, hyperparameter)


if __name__ == '__main__':
    '''
    starts the main function when the file is being called
    '''
    main()
