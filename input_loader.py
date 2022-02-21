"""

@author: guuug
"""

import pandas as pd


class InputLoader():
    """
    loads input from tables and returns it as dataframe or dictionary
    sfh = single family houses
    mfh = many family houses
    th = therasses
    ab = ambitious
    """

    # TODO: Ask Luisa whether this way or another
    def get_linear_dist(self, a, b, c, d, years):
        def get_linear(x, y):
            linear_factor = (y-x)/years
            linear = [x]
            for i in range(years-1):
                linear.append(linear[-1]+linear_factor)
            return linear
        linear = get_linear(a, b)
        lin = get_linear(b, c)
        for i in lin:
            linear.append(i)
        lin = get_linear(c, d)
        for i in lin:
            linear.append(i)
        linear.append(d)
        return linear

    def get_exponential_dist(self, a, b, c, d, years):
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
        - interpolation
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
                    def fun(a, b, c, d, years):
                        return self.get_linear_dist(a, b, c, d, years)
                # exponential interpolation
                elif line['interpolation'] == 'exponential':
                    def fun(a, b, c, d, years):
                        return self.get_exponential_dist(a, b, c, d, years)
                # add params to dict of dicts
                param[scenario][line['parameter']] = fun(line[2020],
                                                              line[2030],
                                                              line[2040],
                                                              line[2050], 10)
        return param
