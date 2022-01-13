"""

@author: guuug
"""

import pandas as pd


class DataLoader():
	"""
	loads all inputs and returns them as dataframe
	"""
	
	def load_csv(self, path_to_csv):
		#read the csv as dataframe
		df = pd.read_csv(path_to_csv)
		return df
		

