"""

@author: guuug
"""

###### IMPORTS ######

import data_loader
import os

###### GLOBALS ######

# demolition and restauration rate of building classes
# TODO: short description where the data originates or how it is calculated
PATH_DISTRIBUTION_BUILDINGS = os.path.join('data','distribution_buildings.csv')

# demographic developement of germany based on different population models
# source: https://www-genesis.destatis.de/genesis//online?operation=table&code=12421-0001&bypass=true&levelindex=0&levelid=1643115777925#abreadcrumb
PATH_DEMOGRAPHIC_DEVELOPEMENT = os.path.join('data','12421-0001.xlsx')

# TODO: short description, link to table
PATH_TABULA = os.path.join('data','TABULA-Analyses_DE-Typology_ResultData.xlsx')

# TODO: add description
PATH_SHARE_BUILDINGS_2019 = os.path.join('data','share_buildings_2019.xlsx')


###### METHODS ######

def load_data(): 
    dl = data_loader.DataLoader()  

    #df_tabula = dl.load_tabula(PATH_TABULA) 
    #df_dem_dev = dl.load_demographic_developement(PATH_DEMOGRAPHIC_DEVELOPEMENT)
    df_share_buildings = dl.load_share_buildings(PATH_SHARE_BUILDINGS_2019)

def main():
    # load all relevant input data from the data loader
    load_data()


if __name__ == '__main__':
    '''
    starts the main function when the file is being called
    '''
    main()
