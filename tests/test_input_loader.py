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

IL = input_loader.INPUTLoader()

SOE = os.path.join(FOLDER_PATH,
                   '..',
                   'input',
                   'parameter_soe.xlsx')


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
        df = IL.load_tabula(SOE)

        # test if file is empty
        self.assertIsNotNone(df)

        # test if all needed parameters are given
        parameters = ['restoration_rate',
                      'restoration_share_amb',
                      'new_building_rate',
                      'new_building_share_sfh',
                      'new_building_share_th',
                      'new_building_share_ah',
                      'demolition_rate',
                      'living_space_pc',
                      'share_restoration_sfh',
                      'share_restoration_th',
                      'share_restoration_ah',
                      'share_demolition_sfh',
                      'share_demolition_ah',
                      'share_demolition_sfh']
        check_column_list = df['parameter'].to_list()
        self.check_in(parameters, check_column_list)

        # ensure that all entries in years differ from zero
        years = ['2020', '2030', '2040', '2050']
        for year in years:
            check_column_list = df[year].to_list()
            for elem in check_column_list:
                self.assertIsNotNone(elem)
                self.assertNotEqual(0)


if __name__ == '__main__':
    unittest.main()
