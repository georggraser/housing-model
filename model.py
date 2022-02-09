"""

@author: guuug
"""

# IMPORTS

import data_loader
import input_loader
import os

# GLOBALS

# Distribution of demolition and restoration rates
# depending on the year of construction
# TODO: genauer raussuchen: own estimations based on bbsr
DISTRIBUTION_BUILDINGS = os.path.join(
                                'data', 'distribution_buildings.csv')

# demographic developement of germany based on different
# population models
# source: https://www-genesis.destatis.de/genesis//online?operation=table&code=12421-0001&bypass=true&levelindex=0&levelid=1643115777925#abreadcrumb
DEMOGRAPHIC_DEVELOPEMENT = os.path.join(
                                'data', '12421-0001.xlsx')

# Building typology data from IWU (Institut Wohnen und Umwelt), https://www.iwu.de/fileadmin/tools/tabula/TABULA-Analyses_DE-Typology_DataTables.zip
TABULA = os.path.join(
    'data', 'TABULA-Analyses_DE-Typology_ResultData.xlsx')

# Weighting of the building typology in 2019 based on a weighted building
# typology from 2011 [1] and supplemented by energetic modernisation [2] and
# new buildings [3] and demolition [3, 4]
# [1] https://www.iwu.de/fileadmin/user_upload/dateien/energie/klima_altbau/Fl%C3%A4chen_Geb%C3%A4udetypologie_Okt_2013.pdf
# [2] https://www.iwu.de/fileadmin/publikationen/gebaeudebestand/2018_IWU_CischinskyEtDiefenbach_Datenerhebung-Wohngeb%C3%A4udebestand-2016.pdf
# [3] TODO: genauer raussuchen: www.destatis.de
# [4] TODO: genauer raussuchen bbsr
SHARE_BUILDINGS_2019 = os.path.join(
    'data', 'share_buildings_2019.xlsx')

# Input data - different scenarios
SOE = os.path.join('input', 'parameter_soe.xlsx')


# METHODS


def load_data():
    dl = data_loader.DataLoader()
    df_tabula = dl.load_tabula(TABULA)
    df_dem_dev = dl.load_demographic_developement(DEMOGRAPHIC_DEVELOPEMENT)
    df_share_buildings = dl.load_share_buildings(SHARE_BUILDINGS_2019)
    return df_tabula, df_dem_dev, df_share_buildings


def load_input():
    il = input_loader.InputLoader()
    _ = il.load_params_soe(SOE)


def main():
    # load all relevant input data from the data loader
    # load_data()
    load_input()


if __name__ == '__main__':
    '''
    starts the main function when the file is being called
    '''
    main()
