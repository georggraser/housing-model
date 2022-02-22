"""

@author: guuug
"""

import unittest
import os
import sys

# this adds the root directory to our path to be able to load data from root
FOLDER_PATH = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(FOLDER_PATH, '..'))
import inputs

# GLOBALS

DL = inputs.DataLoader()

TABULA = os.path.join(FOLDER_PATH,
                      '..',
                      'data',
                      'TABULA-Analyses_DE-Typology_ResultData.xlsx')
DEMOGRAPHIC_DEV = os.path.join(FOLDER_PATH,
                               '..',
                               'data',
                               '12421-0001.xlsx')
SHARE_BUILDINGS = os.path.join(FOLDER_PATH,
                               '..',
                               'data',
                               'share_buildings_2019.xlsx')


class DataLoader_test(unittest.TestCase):

    # little  helper function to check elements against list
    def check_in(self, check_list, check_against):
        for check_element in check_list:
            self.assertIn(check_element, check_against,
                          "{} not in dataframe".format(check_element))

    # assure that the tabula table is loaded and still in it's path
    def test_load_tabula(self):
        # assert that the file that is being loaded exists
        self.assertTrue(os.path.exists(TABULA))
        df = DL.load_tabula(TABULA)

        # test if file is empty
        self.assertIsNotNone(df)

        # test if all building types are in the dataframe
        building_types = ['EFH', 'RH', 'MFH', 'GMH', 'Sub-Typen', ]
        check_column_list = df['building_type'].to_list()
        self.check_in(building_types, check_column_list)

    # assure that the demographic developement table is loaded and still in it's path
    def test_load_demographic_developement(self):
        # assert that the file that is being loaded exists
        self.assertTrue(os.path.exists(DEMOGRAPHIC_DEV))
        df = DL.load_demographic_developement(DEMOGRAPHIC_DEV)

        # test if file is empty
        self.assertIsNotNone(df)

        # test if all building types are in the dataframe
        # zfill does zero padding
        bev_variants = ['BEV-VARIANTE-{}'.format(str(i+1).zfill(2))
                        for i in range(21)]
        bev_models = ['BEV-MODELL-{}'.format(str(i+1).zfill(2))
                      for i in range(9)]
        check_days = ['31.12.20{}'.format(i+19) for i in range(42)]
        variants = df['variants'].to_list()
        headers = df.keys().to_list()

        self.check_in(bev_variants, variants)
        self.check_in(bev_models, variants)
        self.check_in(check_days, headers)

    # assure that the share_buildings table is loaded and still in it's path
    def test_load_share_buildings(self):
        # assert that the file that is being loaded exists
        self.assertTrue(os.path.exists(SHARE_BUILDINGS))
        df = DL.load_share_buildings(SHARE_BUILDINGS)

        # test if file is empty
        self.assertIsNotNone(df)


if __name__ == '__main__':
    unittest.main()
