"""

@author: guuug
"""

import unittest
import os
import sys

# this adds the root directory to our path to be able to load data from root
FOLDER_PATH = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(FOLDER_PATH, '..'))
import data_loader

class DataLoader_test(unittest.TestCase):
  
    # assure that the tabula table is loaded and still in it's path
    def test_load_tabula(self): 
        path_tabula = os.path.join(FOLDER_PATH, 
                        '..', 
                        'data', 
                        'TABULA-Analyses_DE-Typology_ResultData.xlsx')

        # assert that the file that is being loaded exists
        self.assertTrue(os.path.exists(path_tabula))

        dl = data_loader.DataLoader()
        df = dl.load_tabula(path_tabula)    
        
        # test if file is empty
        self.assertIsNotNone(df)

        # test if all building types are in the dataframe
        building_types = ['EFH', 'RH', 'MFH', 'GMH', 'Sub-Typen',]
        check_column_name = 'building_type'
        check_column_list = df[check_column_name].to_list()
        for b_type in building_types:
            self.assertTrue(b_type in check_column_list)
        
  
if __name__ == '__main__':
    unittest.main()