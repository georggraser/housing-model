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
		

	def load_tabula(self, path_to_tabula):
    # TODO: check if the parameters should be changeable in a spreadsheet somewhere
		# and being called from there
		
		# parameters for calling the tabula
		columns = "BB, BC, BH, BN, BO, BL, BM"
		header_names = {"building_type" : "BB",
										"building_code" : "BC", 
										"energy_reference_area" : "BH",
										"heating_provided" : "BN",
										"warm_water_provided" : "BO",
										"heating_need" : "BL",
										"warm_water_need" : "BM"}
		rows_start = 147
		rows_end = 278

		# open tabula with pandas
		df = pd.read_excel(path_to_tabula, sheet_name="DE Tables & Charts", 
                        usecols=columns, skiprows=rows_start-1, 
                        nrows=rows_end-rows_start+1, header=None,
												names=header_names.keys())

		print(df)
		return df
