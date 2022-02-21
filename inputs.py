"""

@author: guuug
"""

from cmath import nan
import pandas as pd


class DataLoader():
    """
    loads data from tables and returns it as dataframe
    """

    def load_share_buildings(self, path_share_buildings):
        df = pd.read_excel(path_share_buildings)
        total_living_space = df['living_space_mio.m2'].sum()
        relative_living_space = [x / total_living_space
                                 for x in df['living_space_mio.m2']
                                 if x is not nan]
        # add a column called 'percent_living_space' and insert
        # calculated values
        df.loc[:, 'percent_living_space'] = relative_living_space
        # print(df.to_markdown())
        return df, total_living_space

    def load_demographic_developement(self, path_demographic_dev):
        # TODO: check if the parameters should be changeable in a spreadsheet
        # somewhere and being called from there

        # parameters for calling the demographic developement
        columns = 'A, C:AR'
        rows_start = 6
        rows_end = 36
        # the not so clean hard-coded variant of names
        names = ['variants'] + ['31.12.20{}'.format(i+19) for i in range(42)]

        df = pd.read_excel(
            path_demographic_dev, usecols=columns, names=names, header=None,
            skiprows=rows_start, nrows=rows_end - rows_start)

        print(df.to_markdown())
        exit(1)
        return df

    def load_tabula(self, path_tabula):
        # TODO: check if the parameters should be changeable in a spreadsheet
        # somewhere and being called from there

        # parameters for calling the tabula
        sheet_name = 'DE Tables & Charts'
        columns_used = {'identifier': 'F',
                        'building_type': 'BB',
                        'building_code': 'BC',
                        'energy_reference_area': 'BH',
                        'heat_provided': 'BN',
                        'building_variant': 'BF',
                        'hot_water_provided': 'BO',
                        'space_heat_need': 'BL',
                        'hot_water_need': 'BM'}
        columns = ''
        names = []
        for key, value in columns_used.items():
            names.append(key)
            if columns == "":
                columns = value
            else:
                columns += ", " + value

        # load the tabula with a little method, params are the start
        # and end line numbers
        def loader(x, y):
            return pd.read_excel(
                path_tabula, sheet_name=sheet_name, usecols=columns,
                skiprows=x-1, nrows=y-x+1, header=None, names=names)

        rows_start_end = [[147, 278], [279, 281], [288, 290], [297, 299],
                          [306, 308], [315, 317], [324, 326]]
        # dataframe with rows from line 147 to 278
        df = loader(rows_start_end[0][0], rows_start_end[0][1])
        # add the rest to the dataframe
        for x, y in rows_start_end[1:]:
            df = df.append(loader(x, y), ignore_index=True)
        # fill nans from merged cells with the correct texts
        df = df.fillna(method='ffill', axis=0)
        # print(df.to_markdown())
        return df


class InputLoader():
    """
    loads input from tables and returns it as dataframe or dictionary
    sfh = single family houses
    mfh = many family houses
    th = therasses
    ab = ambitious
    """

    def get_linear_dist(self, a, b, c, d, e, years, div):
        # check whether divergence is value or list
        if(isinstance(div, str)):
            div_factor = div.split(', ')
            div_factor = [float(i) for i in div_factor]
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

    def get_exponential_dist(self, a, b, c, d, e, years, div):
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
        param = {}
        for scenario in scenarios:
            df_scenario = df.loc[df['scenario'] == scenario]
            param[scenario] = {}
            for i in range(len(df_scenario)):
                line = df_scenario.iloc[i]
                # linear interpolation
                if line['interpolation'] == 'linear':
                    def fun(a, b, c, d, e, years, div):
                        return self.get_linear_dist(a, b, c, d, e, years, div)
                # exponential interpolation
                elif line['interpolation'] == 'exponential':
                    def fun(a, b, c, d, e, years, div):
                        return self.get_exponential_dist(a, b, c, d, e, years,
                                                         div)
                # add params to dict of dicts
                years = [2020, 2030, 2040, 2050, 2060]
                param[scenario][line['parameter']] = fun(line[years[0]],
                                                         line[years[1]],
                                                         line[years[2]],
                                                         line[years[3]],
                                                         line[years[4]],
                                                         years,
                                                         line['divergence'])
        return param

    def load_hyperparameter(self, path_hyperparam):
        df = pd.read_excel(path_hyperparam)
        hyperparameter = {}
        for param, value in zip(df['parameter'], df['value']):
            hyperparameter[param] = value
        return hyperparameter


class RateCalculator():
    """
    calculates the new building rate and the demolition rate
    """

    def rates(self, total_living_space):
        pass

