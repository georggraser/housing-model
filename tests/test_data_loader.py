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
        dl.load_tabula(path_tabula)       
  
if __name__ == '__main__':
    unittest.main()