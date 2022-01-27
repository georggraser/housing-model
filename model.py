"""

@author: guuug
"""

###### IMPORTS ######

import data_loader
import os

###### GLOBALS ######

PATH_MAIN_PARAMETER = os.path.join('data','main_parameter.csv')
PATH_DISTRIBUTION_BUILDINGS = os.path.join('data','distribution_buildings.csv')
PATH_POPULATION = os.path.join('data','population.csv')
PATH_DEMOGRAPHIC_DEVELOPEMENT = os.path.join('data','12421-0001.xlsx')
PATH_TABULA = os.path.join('data','TABULA-Analyses_DE-Typology_ResultData.xlsx')

###### METHODS ######

def load_data(): 
    dl = data_loader.DataLoader()  
    #main_parameter_df = dl.load_csv(PATH_MAIN_PARAMETER)
    #distribution_buildings_df = dl.load_csv(PATH_DISTRIBUTION_BUILDINGS)
    #population_df = dl.load_csv(PATH_POPULATION)
    
    #dl.load_tabula(PATH_TABULA) 
    dl.load_demographic_developement(PATH_DEMOGRAPHIC_DEVELOPEMENT)

def main():
  # load all relevant input data from the data loader
  load_data()


if __name__ == '__main__':
  '''
  starts the main function when the file is being called
  '''
  main()
