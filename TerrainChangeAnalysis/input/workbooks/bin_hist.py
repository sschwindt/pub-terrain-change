import xlrd
import numpy as np
import matplotlib.pyplot as plt
import os
print(os.path.abspath(__file__))
'''
	Input file name and path containing the hourly discharge.
	val.txt holds the bins listed one below the other
	for example:
	500, 1500
	1500, 2500
	Output freq is the duration in minutes. (Here 15)
	Output bins_mid returns mean values of the bins entered


'''

def discharge_bins(file1):

	data_book = xlrd.open_workbook(file1)
	sheet_index = 0
	data_sheet = data_book.sheet_by_index(sheet_index)
	col_index = 2
	data = data_sheet.col(col_index)
	data_list = []
	del data[0:4]
	bins_tuple=[]
	for i in data:
		if(isinstance(i.value, float)):
			data_list.append(i.value)
	with open('val_bin.txt','r') as fp:
		for i in fp.readlines():
			temp = i.split(",")
			try:
				bins_tuple.append((int(temp[0]), int(temp[1])))
			except: pass
		#bins_tuple = map(int, bins_tuple)

	
	bins_mid = [(bins_tuple[j][0]+bins_tuple[j][1]) /2 for j in range(len(bins_tuple))]
	freq = {x:0 for x in bins_mid}
	#print(bins_mid)
	for i in data_list:
		for j in range(len(bins_tuple)):
			if(bins_tuple[j][0]<=i<=bins_tuple[j][1]):
				freq[bins_mid[j]] += 15	#Change addition according to csv time slots. Here 15min.

	
	plt.bar(np.arange(len(freq.keys())), freq.values(), align = 'center', alpha = 0.5)
	plt.xticks(np.arange(len(freq.keys())), freq.keys(), rotation = 70)
	plt.show()

	return freq, bins_mid


if __name__ == '__main__':
        discharge_bins(os.path.abspath(__file__) + "/MRY_hourly_Event_20083112_20140513.xlsx")

