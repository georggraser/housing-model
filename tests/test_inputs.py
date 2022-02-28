"""

@author: guuug
"""

import unittest
import os
import sys
import pandas as pd

# this adds the root directory to our path to be able to load data from root
FOLDER_PATH = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(FOLDER_PATH, '..'))
import inputs

# GLOBALS

DATA = os.path.join(FOLDER_PATH, '..', 'data')
INPUT = os.path.join(FOLDER_PATH, '..', 'input')

TABULA = os.path.join(DATA, 'TABULA-Analyses_DE-Typology_ResultData.xlsx')
DEMOGRAPHIC_DEV = os.path.join(DATA, '12421-0001.xlsx')
SHARE_BUILDINGS = os.path.join(DATA, 'share_buildings_2019.xlsx')
SCENARIOS = os.path.join(INPUT, 'parameter_scenarios.xlsx')
HYPERPARAMETER = os.path.join(INPUT, 'hyperparameter.xlsx')

DL = inputs.DataLoader()
IL = inputs.InputLoader()


# little  helper function to check elements against list
def check_in(self, check_list, check_against):
    for check_element in check_list:
        self.assertIn(check_element, check_against,
                      "{} not in dataframe".format(check_element))


class DataLoader_test(unittest.TestCase):

    def __init__(self):
        # on object creation check if all relevant paths are valid
        self.assertTrue(os.path.exists(TABULA))
        self.assertTrue(os.path.exists(DEMOGRAPHIC_DEV))
        self.assertTrue(os.path.exists(SHARE_BUILDINGS))
        # load paths to class-instances
        self.tabula = TABULA
        self.demographic_dev = DEMOGRAPHIC_DEV
        self.share_buildings = SHARE_BUILDINGS

    # assure that the tabula table is loaded and still in it's path
    def test_load_tabula(self):
        # assert that the file that is being loaded exists
        df = DL.load_tabula(self.tabula)

        # test if file is empty
        self.assertIsNotNone(df)

        # test if all building types are in the dataframe
        building_types = ['EFH', 'RH', 'MFH', 'GMH', 'Sub-Typen', ]
        check_column_list = df['building_type'].to_list()
        check_in(self, building_types, check_column_list)

    # assure that the demographic dev table is loaded and still in it's path
    def test_load_demographic_developement(self):
        # first: check file
        columns = 'A, D:AR'
        rows_start = 5
        rows_end = 35
        df = pd.read_excel(
            self.demographic_dev, usecols=columns,
            skiprows=rows_start, nrows=rows_end - rows_start)
        df.rename(columns={'Unnamed: 0': 'bev_variants'}, inplace=True)

        # test if file is empty
        self.assertIsNotNone(df)

        # test if all building types are in the dataframe
        # zfill does zero padding
        bev_variants = ['BEV-VARIANTE-{}'.format(str(i+1).zfill(2))
                        for i in range(21)]
        bev_models = ['BEV-MODELL-{}'.format(str(i+1).zfill(2))
                      for i in range(9)]
        bev_all = bev_variants + bev_models
        year_start = 2020
        year_end = 2060
        year_range = year_end-year_start+1
        check_days = ['31.12.{}'.format(i+year_start)
                      for i in range(year_range)]
        variants = df['bev_variants'].to_list()
        headers = df.keys().to_list()

        check_in(self, bev_all, variants)
        check_in(self, check_days, headers)

        # second: check funktion
        dem_dev = DL.load_demographic_developement(self.demographic_dev)
        check_in(self, bev_all, dem_dev.keys())

        for values in dem_dev.values():
            self.assertEqual(len(values), year_range)

    # assure that the share_buildings table is loaded and still in it's path
    def test_load_share_buildings(self):
        df, total_ls = DL.load_share_buildings(self.share_buildings)

        # test if file is empty
        self.assertIsNotNone(df)
        self.assertIsNotNone(total_ls)


class InputLoader_test(unittest.TestCase):

    def __init__(self):
        # on object creation check if all relevant paths are valid
        self.assertTrue(os.path.exists(SCENARIOS))
        self.assertTrue(os.path.exists(HYPERPARAMETER))
        # load paths to class-instances
        self.scenarios = SCENARIOS
        self.hyperparameter = HYPERPARAMETER

    # assure that the tabula table is loaded and still in it's path
    def test_load_param(self):
        # check the file first
        df = pd.read_excel(self.scenarios)
        # test if file is empty
        self.assertIsNotNone(df)
        keys = ['scenario', 'parameter', 2020, 2030, 2040, 2050, 2060,
                'interpolation', 'divergence']
        # check if given keys are in dataframe
        check_in(self, keys, df.keys())
        # check if given scenarios are in dataframe
        scenarios = ['soe', 'sme']
        df_scenarios = df[keys[0]].to_list()
        check_in(self, scenarios, df_scenarios)
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
                          'demolition_rate_min',
                          'demolition_sfh',
                          'demolition_th',
                          'demolition_mfh',
                          'demolition_ab',
                          'new_building_rate_min',
                          'new_building_share_sfh',
                          'new_building_share_th',
                          'new_building_share_mfh',
                          'new_building_share_ab',
                          'living_space_pc']
            check_in(self, parameters, check_column_list)
            # ensure that all entries in years differ from zero
            for year in keys[2:5]:
                check_column_list = df_scenario[year].to_list()
                for elem in check_column_list:
                    self.assertIsNotNone(elem)
                    self.assertNotEqual(elem, 0)
            # ensure that interpolations in dataframe match with given ones
            interpolations = df_scenario[keys[-2]].to_list()
            interpolations_allowed = ['linear', 'exponential']
            check_in(self, interpolations, interpolations_allowed)

            # check divergence
            def divergence_checker(div):
                self.assertLessEqual(div, 1)
                self.assertGreaterEqual(div, 0)
            for div in df[keys[-1]]:
                if(isinstance(div, str)):
                    self.assertIn(',', div)
                    div_factor = div.split(',')
                    div_factor = [float(i.strip()) for i in div_factor]
                    for div2 in div_factor:
                        divergence_checker(div2)
                else:
                    divergence_checker(div)

        # second check the loaded dict
        scen_params = IL.load_param(self.scenarios)
        for key, value in scen_params.items():
            self.assertIn(key, scenarios)
            for ke, val in value.items():
                self.assertIn(ke, parameters)
                self.assertIsInstance(val, list)
                for va in val:
                    self.assertIsNotNone(va)

    def test_load_hyperparameter(self):
        hyper = IL.load_hyperparameter(self.hyperparameter)
        keys = ['bev_variant', 'scenario']
        for key, value in hyper.items():
            self.assertIn(key, keys)
            self.assertIsNotNone(value)


if __name__ == '__main__':
    unittest.main()
