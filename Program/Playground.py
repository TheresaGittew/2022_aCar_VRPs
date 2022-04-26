from Program.Deprecated import DEPR_ReadNilsInputFiles as dp, SETUP_and_IO as setio
import numpy as np
from itertools import combinations

A = ['Ernie', 'Bert', 'Bibo']
B = ['green', 'yellow', 'blue']
C = [4,8, 14]
path_demand_file = '/GIS_Data/Deprecated/11-19-21_EXAMPLE_DemandList2.csv'
path_results = 'Deprecated/Results/Scenario_NumVec2-LBs35-UBs80/DecisionvariableValues.xlsx'


# total_demands_nested_dict, daily_max_demand_nested_dict = dp.read_demands(path_demand_file,
#                                                                               demand_type_names=['PNC', 'WDS'])
# print(total_demands_nested_dict)
#
# print(sum(list(map(lambda x: x['PNC'],list(total_demands_nested_dict.values())))))
# print(185 / 8)
#
# pd_x = setio.get_x_df(path_results)
#
# res = list(pd_x.query('Day == ' + str(2))['RouteId'])
# print(res)

#
# self.fpvrp_obj.setObjective(
#             sum(sum(sum(self.x[r, t] * self.cfg.c[i, j] for (i, j) in self.cfg.E_r[r]) for r in self.cfg.R_ids) for t in self.cfg.T))
#
# # 1368


a =  [[(7, 55), (25, 100), (55, 7), (100, 25)], [(9, 100), (13, 36), (36, 13), (100, 9)], [(9, 100), (13, 36), (36, 13), (100, 9)], [(10, 33), (33, 10), (50, 100), (100, 50)], [(13, 36), (36, 13), (50, 100), (100, 50)], [(13, 36), (25, 100), (36, 13), (100, 25)], [(14, 43), (43, 14), (50, 100), (100, 50)], [(21, 100), (37, 57), (57, 37), (100, 21)], [(24, 48), (25, 100), (48, 24), (100, 25)], [(25, 100), (35, 52), (52, 35), (100, 25)], [(37, 57), (38, 100), (57, 37), (100, 38)], [(2, 100), (9, 25), (25, 9), (100, 2)], [(7, 50), (29, 100), (50, 7), (100, 29)], [(9, 37), (37, 9), (42, 100), (100, 42)], [(9, 35), (15, 100), (35, 9), (100, 15)], [(9, 52), (16, 100), (52, 9), (100, 16)], [(15, 100), (33, 48), (48, 33), (100, 15)], [(16, 36), (28, 100), (36, 16), (100, 28)], [(16, 100), (33, 43), (43, 33), (100, 16)], [(16, 100), (29, 40), (40, 29), (100, 16)], [(16, 100), (36, 40), (40, 36), (100, 16)], [(20, 57), (45, 100), (57, 20), (100, 45)], [(13, 40), (14, 33), (33, 100), (40, 13), (100, 14)], [(14, 24), (24, 100), (37, 52), (52, 37), (100, 14)], [(16, 45), (25, 57), (45, 100), (57, 25), (100, 16)], [(2, 38), (25, 100), (37, 25), (38, 2), (100, 37)], [(13, 21), (15, 38), (21, 13), (38, 100), (100, 15)], [(21, 50), (40, 45), (45, 40), (50, 100), (100, 21)], [(28, 42), (29, 45), (42, 100), (45, 29), (100, 28)], [(9, 57), (57, 9)], [(9, 57), (57, 9)]] #[[(7, 55), (25, 100), (55, 7), (100, 25)], [(9, 100), (13, 36), (36, 13), (100, 9)], [(9, 100), (13, 36), (36, 13), (100, 9)], [(10, 33), (33, 10), (50, 100), (100, 50)], [(13, 36), (36, 13), (50, 100), (100, 50)], [(13, 36), (25, 100), (36, 13), (100, 25)], [(14, 43), (43, 14), (50, 100), (100, 50)], [(21, 100), (37, 57), (57, 37), (100, 21)], [(24, 48), (25, 100), (48, 24), (100, 25)], [(25, 100), (35, 52), (52, 35), (100, 25)], [(37, 57), (38, 100), (57, 37), (100, 38)], [(2, 100), (9, 25), (25, 9), (100, 2)], [(7, 50), (29, 100), (50, 7), (100, 29)], [(9, 37), (37, 9), (42, 100), (100, 42)], [(9, 35), (15, 100), (35, 9), (100, 15)], [(9, 52), (16, 100), (52, 9), (100, 16)], [(15, 100), (33, 48), (48, 33), (100, 15)], [(16, 36), (28, 100), (36, 16), (100, 28)], [(16, 100), (33, 43), (43, 33), (100, 16)], [(16, 100), (29, 40), (40, 29), (100, 16)], [(16, 100), (36, 40), (40, 36), (100, 16)], [(20, 57), (45, 100), (57, 20), (100, 45)], [(13, 40), (14, 33), (33, 100), (40, 13), (100, 14)], [(14, 24), (24, 100), (37, 52), (52, 37), (100, 14)], [(16, 45), (25, 57), (45, 100), (57, 25), (100, 16)], [(15, 24), (16, 36), (24, 15), (36, 40), (40, 100), (100, 16)], [(2, 20), (20, 100), (40, 45), (45, 40), (100, 2)], [(9, 57), (10, 100), (48, 10), (57, 9), (100, 48)], [(40, 45), (45, 100), (50, 55), (55, 50), (100, 40)], [(2, 38), (21, 50), (38, 2), (50, 100), (100, 21)], [(7, 21), (21, 7), (25, 37), (37, 100), (100, 25)], [(7, 14), (14, 7), (21, 100), (50, 21), (100, 50)], [(9, 40), (10, 24), (24, 10), (40, 100), (100, 9)], [(9, 100), (10, 15), (15, 10), (40, 9), (100, 40)], [(13, 16), (14, 48), (16, 13), (48, 100), (100, 14)], [(21, 50), (35, 57), (50, 100), (57, 35), (100, 21)], [(25, 37), (29, 45), (37, 100), (45, 29), (100, 25)], [(7, 43), (21, 55), (43, 7), (55, 100), (100, 21)], [(21, 100), (35, 37), (37, 35), (55, 21), (100, 55)], [(13, 29), (20, 100), (25, 20), (29, 13), (100, 25)], [(7, 50), (25, 38), (38, 25), (43, 7), (50, 100), (100, 43)], [(9, 100), (13, 45), (20, 57), (45, 13), (57, 9), (100, 20)], [(14, 43), (21, 100), (33, 14), (42, 21), (43, 33), (100, 42)], [(7, 33), (25, 35), (33, 7), (35, 52), (52, 100), (100, 25)], [(10, 14), (14, 10), (24, 33), (33, 100), (100, 24)], [(21, 48), (29, 36), (36, 29), (48, 100), (100, 21)], [(36, 45), (42, 100), (45, 36), (50, 42), (100, 50)], [(16, 35), (35, 16), (40, 52), (52, 100), (100, 40)], [(13, 29), (21, 100), (28, 21), (29, 45), (45, 13), (100, 28)], [(9, 29), (20, 100), (28, 20), (29, 9), (100, 28)], [(7, 42), (21, 7), (28, 100), (42, 21), (50, 28), (100, 50)], [(15, 21), (21, 100), (36, 38), (38, 48), (48, 36), (100, 15)], [(25, 57), (29, 100), (38, 40), (40, 38), (57, 29), (100, 25)]]
a2 = [set(map(lambda x: x[0], i)) for i in a]
print(a2)
lis = []
for i in a2:
    count = 0
    for i_2 in a2:
        if i_2 == i:
            count += 1

    lis.append(count)

#print(lis)


c =  [[(7, 21), (9, 35), (21, 7), (25, 9), (35, 100), (100, 25)], [(10, 48), (16, 100), (40, 45), (45, 16), (48, 10), (100, 40)]]
c2 =  [set(map(lambda x: x[0], i)) for i in c]

print(([True for c in c2 if c in a2 ]))

import pandas as pd
# INPUT File Nils:
path = '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/ET_Location_Data.csv'
#     ClusterId          WDS         ELEC           ED          ANC
# 0           2  2806,157477   6841,00195  1637,105397  403,7666044
# 1           4  1501,658731  2221,451024  565,6702209  339,2385783
# 2           7  760,7570588   3662,22699   1060,60763  1107,927395

# pds_narrow = pds_csv.melt(id_vars='ClusterId', var_name='Service_type')


pds_csv = pd.read_csv(path, delimiter=';')
# print (pds_csv)
#
# pds_narrow = pds_csv.melt(id_vars='ClusterId', var_name='Service_type')
#
# print(pds_narrow)
# pds_cols_to_indices = pds_narrow.set_index(['ClusterId','Service_type'])
# print(pds_cols_to_indices)
#
# relevant_rows = pds_cols_to_indices.loc[(2),:]
# print(pds_cols_to_indices)
# print("LOC")
# print(relevant_rows)
# res = pds_cols_to_indices.drop(index =('WDS'), level=1)
# print(res)

# dict = pds_cols_to_indices.to_dict()


# generates a dictionary for each column, with indices as keys.
# As we have only 1 column remaining, we should use this one.
#inner_dict = dict['value']
#print(inner_dict)

# Result:
# {(2, 'WDS'): '2806,157477', (4, 'WDS'): '1501,658731', (7, 'WDS'): '760,7570588', (9, 'WDS'): '11219,11949', (10, 'WDS'): '13029,79209', (11, 'WDS'): '549,1227201', (12, 'WDS'): '1368,525571', (13, 'WDS'): '3902,569111', (14, 'WDS'): '3138,069886', (15, 'WDS'): '3405,779024', (16, 'WDS'): '2042,401477', (20, 'WDS'): '284,5119135', (21, 'WDS'): '605,7323486', (22, 'WDS'): '7324,498321', (24, 'WDS'): '3749,602426', (25, 'WDS'): '4262,913102', (27, 'WDS'): '5568,744156', (28, 'WDS'): '2746,902945', (29, 'WDS'): '1808,746963', (30, 'WDS'): '1838,621175', (32, 'WDS'): '5991,470312', (33, 'WDS'): '8242,540054', (34, 'WDS'): '580,7872619', (35, 'WDS'): '3342,460004', (36, 'WDS'): '4148,466617', (37, 'WDS'): '1380,173565', (38, 'WDS'): '1028,567049', (40, 'WDS'): '795,446064', (41, 'WDS'): '4861,384368', (42, 'WDS'): '1701,227193', (43, 'WDS'):


# pds_csv_with_multi = pds_csv.set_index(['ClusterId','WDS','ELEC'])
# print(pds_csv_with_multi)
# #pds_csv_with_multi.drop(index=('11219,11949', '12569,86931'), level=1,  inplace=True)
# #print(pds_csv_with_multi.loc[2])
#
# ind = pds_csv_with_multi.index[(pds_csv_with_multi['ED']=='1637,105397') & (pds_csv_with_multi['PNC']=='403,7666044')].tolist()
# print("Found this" , ind)
# pds_csv_with_multi.drop(index=ind, inplace=True)
# print(pds_csv_with_multi)
#
# print(np.sqrt([9]))


print(list(combinations([0,1,2,3,4], r=2)))