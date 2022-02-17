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
            return [(y-x)/years for i in range(years)]
        linear1 = get_linear(a, b)
        linear2 = get_linear(b, c)
        linear3 = get_linear(c, d)
        # this joins the list items together
        return [*linear1, *linear2, *linear3]

    def get_exponential_dist(self, a, b, c, d, years):
        pass

    def load_params_soe(self, path_params_soe):
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
        df = pd.read_excel(path_params_soe)
        # get given scenarios
        scenarios = [scenario for scenario in df['scenario']]
        # remove duplicates (a set does not contain duplicates)
        scenarios = list(set(scenarios))
        params_soe = {}
        for scenario in scenarios:
            df_scenario = df.loc[df['scenario'] == scenario]
            params_soe[scenario] = {}
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
                params_soe[scenario][line['parameter']] = fun(line[2020],
                                                              line[2030],
                                                              line[2040],
                                                              line[2050], 10)
        return params_soe
