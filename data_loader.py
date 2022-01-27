"""

@author: guuug
"""

import pandas as pd


class DataLoader():
    """
    loads all inputs and returns them as dataframe
    """

    def load_demographic_developement(self, path_demographic_dev):
        # TODO: check if the parameters should be changeable in a spreadsheet somewhere
        # and being called from there

        # parameters for calling the demographic developement
        columns = 'A, C:AR'
        rows_start = 6
        rows_end = 36
        # the not so clean hard-coded variant of names
        names = ['variants'] + ['31.12.20{}'.format(i+19) for i in range(42)]

        df = pd.read_excel(
            path_demographic_dev, usecols=columns, names=names, header=None,
            skiprows=rows_start, nrows=rows_end - rows_start)

        #print(df)
        return df


    def load_tabula(self, path_tabula):
        # TODO: check if the parameters should be changeable in a spreadsheet somewhere
        # and being called from there

        # parameters for calling the tabula
        sheet_name = 'DE Tables & Charts'
        columns_used = {'building_type' : 'BB',
                        'building_code' : 'BC', 
                        'energy_reference_area' : 'BH',
                        'heat_provided' : 'BN',
                        'building_variant' : 'BF',
                        'hot_water_provided' : 'BO',
                        'space_heat_need' : 'BL',
                        'hot_water_need' : 'BM'}
        columns = ''
        names = []
        for key, value in columns_used.items():
            names.append(key)
            if columns is "":
                columns = value
            else: 
                columns += ", " + value

        # load the tabula with a little method, params are the start
        # and end line numbers
        def loader(x,y): 
            return pd.read_excel(
                path_tabula, sheet_name=sheet_name, usecols=columns, 
                skiprows=x-1, nrows=y-x+1, header=None, names=names)
            
        rows_start_end = [[147, 278], [279, 281], [288, 290], [297, 299], 
                            [306, 308], [315, 317],[324, 326]]
        # dataframe with rows from line 147 to 278
        df = loader(rows_start_end[0][0], rows_start_end[0][1])
        # add the rest to the dataframe
        for x, y in rows_start_end[1:]:
            df = df.append(loader(x,y), ignore_index=True)
        # fill nans from merged cells with the correct texts
        df = df.fillna(method='ffill', axis=0)
        #print(df.to_markdown())
        return df
