"""

@author: guuug
"""

import data_loader

###### GLOBALS ######

MAIN_PARAMETER = 'data/main_parameter.csv'
DISTRIBUTION_BUILDINGS = 'data/distribution_buildings.csv'
POPULATION = 'data/population.csv'


def main():
  # load all relevant input data from the data loader
  dl = data_loader.DataLoader()
  main_parameter_df = dl.load_csv(MAIN_PARAMETER)
  distribution_buildings_df = dl.load_csv(DISTRIBUTION_BUILDINGS)
  population_df = dl.load_csv(POPULATION)
  
  print(distribution_buildings_df)


if __name__ == '__main__':
  '''
  starts the main function when the file is being called
  '''
  main()
