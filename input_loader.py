"""

@author: guuug
"""

import pandas as pd


class InputLoader():
    """
    loads input from tables and returns it as dataframe or dictionary
    sfh = single family houses
    th = therasses
    ah = appartments
    amb = ambitious
    """

    def load_params_soe(self, path_params_soe):
        df = pd.read_excel(path_params_soe)
        return df
