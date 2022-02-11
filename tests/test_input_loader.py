"""

@author: guuug
"""

import unittest
import os
import sys

# this adds the root directory to our path to be able to load data from root
FOLDER_PATH = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(FOLDER_PATH, '..'))
import input_loader

# GLOBALS

IL = input_loader.InputLoader()

SOE = os.path.join(FOLDER_PATH,
                   '..',
                   'input',
                   'parameter_scenarios.xlsx')


class InputLoader_test(unittest.TestCase):

    # little  helper function to check elements against list
    def check_in(self, check_list, check_against):
        for check_element in check_list:
            self.assertIn(check_element, check_against,
                          "{} not in dataframe".format(check_element))

    # assure that the tabula table is loaded and still in it's path
    def test_load_params_soe(self):
        # assert that the file that is being loaded exists
        self.assertTrue(os.path.exists(SOE))
        df = IL.load_params_soe(SOE)
        # test if file is empty
        self.assertIsNotNone(df)
        keys = ['scenario', 'parameter', 2020, 2030, 2040, 2050,
                'interpolation']
        # check if given keys are in dataframe
        self.check_in(keys, df.keys())
        # check if given scenarios are in dataframe
        scenarios = ['soe', 'sme']
        df_scenarios = df[keys[0]].to_list()
        self.check_in(scenarios, df_scenarios)
        # check dataframe for null/nan rows (not allowed)
        self.assertFalse(df.isnull().values.any())
        # iterate through scenarios and limit dataframe each time to single 
        # scenario - ensure to check each scenario
        for scenario in scenarios:
            df_scenario = df.loc[df[keys[0]] == scenario]
            # check if given parameters are in dataframe
            check_column_list = df_scenario[keys[1]].to_list()
            parameters = ['restoration_rate',
                          'restoration_deep_amb',
                          'restoration_sfh',
                          'restoration_th',
                          'restoration_mfh',
                          'restoration_ab',
                          'demolition_rate',
                          'demolition_sfh',
                          'demolition_th',
                          'demolition_mfh',
                          'demolition_ab',
                          'new_building_rate',
                          'new_building_share_sfh',
                          'new_building_share_th',
                          'new_building_share_mfh',
                          'new_building_share_ab',
                          'living_space_pc']
            self.check_in(parameters, check_column_list)
            # ensure that all entries in years differ from zero
            for year in keys[2:5]:
                check_column_list = df_scenario[year].to_list()
                for elem in check_column_list:
                    self.assertIsNotNone(elem)
                    self.assertNotEqual(elem, 0)
            # ensure that interpolations in dataframe match with given ones
            interpolations = df_scenario[keys[-1]].to_list()
            interpolations_allowed = ['linear', 'exponential', 'gauss']
            self.check_in(interpolations, interpolations_allowed)


if __name__ == '__main__':
    unittest.main()
