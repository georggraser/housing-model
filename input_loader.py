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

    def get_linear_dist(a, b, years=10):
        yearly_factor = (b-a)/years
        linear = [yearly_factor for i in range(years)]
        return linear

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
        for scenario in scenarios:
            df_scenario = df.loc[df['scenario'] == scenario]
            # linear
        return df
