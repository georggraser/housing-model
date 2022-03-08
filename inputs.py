"""

@author: guuug
"""

from cmath import nan
import pandas as pd


class DataLoader():
    """
    loads data from tables and returns it as dataframe
    """

    # TODO: add to tests, check that sum == 1
    def load_dist_buildings(self, path_dist_build):
        df = pd.read_excel(path_dist_build)
        return df

    def load_share_buildings(self, path_share_buildings):
        df = pd.read_excel(path_share_buildings)
        total_living_space_2019 = df['living_space_mio.m2'].sum()
        relative_living_space = [x / total_living_space_2019
                                 for x in df['living_space_mio.m2']
                                 if x is not nan]
        # add a column called 'percent_living_space' and insert
        # calculated values
        df.loc[:, 'percent_living_space'] = relative_living_space
        return df, total_living_space_2019

    def load_demographic_developement(self, path_demographic_dev):
        # TODO: check if the parameters should be changeable in a spreadsheet
        # somewhere and being called from there

        # parameters for calling the demographic developement
        columns = 'A, D:AR'
        rows_start = 5
        rows_end = 35
        df = pd.read_excel(
            path_demographic_dev, usecols=columns,
            skiprows=rows_start, nrows=rows_end - rows_start)
        df.rename(columns={'Unnamed: 0': 'bev_variants'}, inplace=True)

        # dataframe in dictionary and change unit from thousand to million
        dem_dev = {}
        factor = 1000
        for i in range(len(df)):
            line = df.iloc[i]
            key = line['bev_variants']
            value = list(line[1:])
            value = [val/factor for val in value]
            dem_dev[key] = value
        return dem_dev

    def load_tabula(self, path_tabula):
        # TODO: check if the parameters should be changeable in a spreadsheet
        # somewhere and being called from there

        # parameters for calling the tabula
        sheet_name = 'DE Tables & Charts'
        # {own assigned name: [tabula name, class]}
        columns_used = {'identifier': ['F', str],
                        'building_type': ['BB', str],
                        'building_code': ['BC', str],
                        'building_variant': ['BF', str],
                        'energy_reference_area': ['BH', float],
                        'space_heat_need': ['BL', float],
                        'hot_water_need': ['BM', float],
                        'heat_provided': ['BN', float],
                        'hot_water_provided': ['BO', float]}
        # load data from columns_used in the correct format
        dtype = {}
        columns = ''
        names = []
        for key, value in columns_used.items():
            dtype[key] = value[1]
            names.append(key)
            if columns == '':
                columns = str(value[0])
            else:
                columns += ',' + str(value[0])

        # load the tabula with a little method, params are the start
        # and end line numbers
        def loader(x, y):
            return pd.read_excel(
                path_tabula, sheet_name=sheet_name, usecols=columns,
                skiprows=x-1, nrows=y-x+1, header=None, names=names,
                dtype=dtype)

        # TODO: check if this is the best way to load data :)
        rows_start_end = [[147, 278], [279, 281], [288, 290], [297, 299],
                          [306, 308], [315, 317], [324, 326]]
        # dataframe with rows from line 147 to 278
        df = loader(rows_start_end[0][0], rows_start_end[0][1])
        # add the rest to the dataframe
        for x, y in rows_start_end[1:]:
            df = df.append(loader(x, y), ignore_index=True)
        # fill nans from merged cells with the correct texts
        df = df.fillna(method='ffill', axis=0)
        return df


class InputLoader():
    """
    loads input from tables and returns it as dataframe or dictionary
    sfh = single family houses
    mfh = many family houses
    th = therasses
    """
    def get_linear_interpolation(self, a, b, c, d, e, years, div):
        # check whether divergence is value or list
        if(isinstance(div, str)):
            div_factor = div.split(',')
            div_factor = [float(i.strip()) for i in div_factor]
            div_str = True
        else:
            div_factor = [div]
            div_str = False
        div_factor = [1 - i for i in div_factor]

        def div_years(x, y, div_fact):
            return (y - x) * div_fact + x

        def get_linear(x, y, years_diff):
            # y_new = div_years(x, y)
            linear_factor = (y - x) / years_diff
            linear = [x]
            for _ in range(years_diff-1):
                linear.append(linear[-1]+linear_factor)
            return linear

        b = div_years(a, b, div_factor[0])
        if div_str is False:
            c = div_years(a, c, div_factor[0])
            d = div_years(a, d, div_factor[0])
            d = div_years(a, e, div_factor[0])
        else:
            c = div_years(a, c, div_factor[1])
            d = div_years(a, d, div_factor[2])
            d = div_years(a, e, div_factor[3])
        linear = get_linear(a, b, years[1]-years[0]) \
            + get_linear(b, c, years[2]-years[1]) \
            + get_linear(c, d, years[3]-years[2]) \
            + get_linear(d, e, years[4]-years[3])
        linear.append(e)
        return linear

    # @TODO: implement exponential interpolation
    def get_exponential_interpolation(self, a, b, c, d, e, years, div):
        pass

    def load_param(self, path_param):
        """
        input headers:
        - scenario
        - parameter
        - 2020
        - 2030
        - 2040
        - 2050
        - 2060
        - interpolation
        - divergence
        """
        df = pd.read_excel(path_param)
        # get given scenarios
        scenarios = [scenario for scenario in df['scenario']]
        # remove duplicates (a set does not contain duplicates)
        scenarios = list(set(scenarios))
        scen_params = {}
        for sc in scenarios:
            df_scenario = df.loc[df['scenario'] == sc]
            scen_params[sc] = {}
            for i in range(len(df_scenario)):
                line = df_scenario.iloc[i]
                # linear interpolation
                if line['interpolation'] == 'linear':
                    def fun(a, b, c, d, e, years, div):
                        return self.get_linear_interpolation(a, b, c, d, e,
                                                             years, div)
                # exponential interpolation
                elif line['interpolation'] == 'exponential':
                    def fun(a, b, c, d, e, years, div):
                        return self.get_exponential_interpolation(a, b, c, d,
                                                                  e, years,
                                                                  div)
                # add params to dict of dicts
                years = [2020, 2030, 2040, 2050, 2060]
                scen_params[sc][line['parameter']] = fun(line[years[0]],
                                                         line[years[1]],
                                                         line[years[2]],
                                                         line[years[3]],
                                                         line[years[4]],
                                                         years,
                                                         line['divergence'])
        return scen_params

    def load_hyperparameter(self, path_hyperparam):
        df = pd.read_excel(path_hyperparam)
        hyperparameter = {}
        seperator = ','
        for i in range(len(df)):
            line = df.iloc[i]
            key = line['parameter']
            value = line['value']
            if key == 'scenario':
                scen = value.split(seperator)
                hyperparameter[key] = [el.strip().lower() for el in scen]
            elif key == 'restauration_building_type bias':
                value = value.lower()
                hyperparameter[key] = value
            else:
                hyperparameter[key] = value
        return hyperparameter


class RateCalculator():
    """
    calculates the new building rate and the demolition rate
    """

    def rates(self, total_living_space_2019, bev, scen_params):
        demolition_rate_min = scen_params['demolition_rate_min']
        new_building_rate_min = scen_params['new_building_rate_min']
        living_space_pc = scen_params['living_space_pc']

        # calculate total living space for the whole timespan
        total_living_space = [total_living_space_2019]
        for pop, ls_pc in zip(bev, living_space_pc):
            total_living_space.append(pop*ls_pc)
        # calc living space from min (new_building_rate and demolition_rate)
        calc_living_space = [total_living_space_2019]
        for i, (nbr_min, dr_min) in enumerate(zip(new_building_rate_min,
                                                  demolition_rate_min)):
            tmp_living_space = total_living_space[i] * (1 + nbr_min - dr_min)
            calc_living_space.append(tmp_living_space)
        # compare total and calc_living_space
        new_building_rate = []
        demolition_rate = []
        for i, (total, calc) in enumerate(zip(total_living_space,
                                              calc_living_space)):
            # case i=0: year 2019 - we needed data from 2018 - we don't need
            if i > 0:
                diff_rate = (total - calc) / total_living_space[i-1]
                if diff_rate > 0:
                    # case too few buildings
                    new_building_rate.append(new_building_rate_min[i-1]
                                             + diff_rate)
                    demolition_rate.append(demolition_rate_min[i-1])
                elif diff_rate < 0:
                    # case too many buildingsa
                    demolition_rate.append(demolition_rate_min[i-1]
                                           - diff_rate)
                    new_building_rate.append(new_building_rate_min[i-1])
                else:
                    # case unrealistic
                    demolition_rate.append(demolition_rate_min[i-1])
                    new_building_rate.append(new_building_rate_min[i-1])

                # TODO Georg: übertragen in test
                # test_living_space = total_living_space[i-1] *
                # (1 + new_building_rate[i-1] - demolition_rate[i-1])
                # null_test = total_living_space[i] - test_living_space
                # print('{}: null-test: {}'.format(i+1, null_test))
        scen_params['demolition_rate'] = demolition_rate
        scen_params['new_building_rate'] = new_building_rate
        scen_params['total_living_space'] = total_living_space
        return scen_params
