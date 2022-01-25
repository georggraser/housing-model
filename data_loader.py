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
		columns_used = {"building_type" : "BB",
										"building_code" : "BC", 
										"energy_reference_area" : "BH",
										"heat_provided" : "BN",
										"hot_water_provided" : "BO",
										"space_heat_demand" : "BL",
										"hot_water_demand" : "BM"}
		columns = ""
		headers = []
		for key, value in columns_used.items():
			headers.append(key)
			if columns is "":
				columns = value
			else: 
				columns += ", " + value
				
		rows_start = 147
		rows_end = 278

		# open tabula with pandas
		df = pd.read_excel(path_to_tabula, sheet_name="DE Tables & Charts", 
                        usecols=columns, skiprows=rows_start-1, 
                        nrows=rows_end-rows_start+1, header=None,
												names=headers)

		print(df)
		return df
