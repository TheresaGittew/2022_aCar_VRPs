import pandas as pd
# INPUT File Nils:
path = '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/ET_Location_Data.csv'
#     ClusterId          WDS         ELEC           ED          ANC
# 0           2  2806,157477   6841,00195  1637,105397  403,7666044
# 1           4  1501,658731  2221,451024  565,6702209  339,2385783
# 2           7  760,7570588   3662,22699   1060,60763  1107,927395

# pds_narrow = pds_csv.melt(id_vars='ClusterId', var_name='Service_type')


pds_csv = pd.read_csv(path, delimiter=';')
print (pds_csv)

pds_narrow = pds_csv.melt(id_vars='ClusterId', var_name='Service_type')

print(pds_narrow)
pds_cols_to_indices = pds_narrow.set_index(['ClusterId','Service_type'])
print(pds_cols_to_indices)
relevant_rows = pds_cols_to_indices.loc[(2),:]
print(pds_cols_to_indices)
#print(relevant_rows)
res = pds_cols_to_indices.drop(index =('WDS'), level=1)
print(res)

dict = pds_cols_to_indices.to_dict()


# generates a dictionary for each column, with indices as keys.
# As we have only 1 column remaining, we should use this one.
inner_dict = dict['value']
#print(inner_dict)

# Result:
# {(2, 'WDS'): '2806,157477', (4, 'WDS'): '1501,658731', (7, 'WDS'): '760,7570588', (9, 'WDS'): '11219,11949', (10, 'WDS'): '13029,79209', (11, 'WDS'): '549,1227201', (12, 'WDS'): '1368,525571', (13, 'WDS'): '3902,569111', (14, 'WDS'): '3138,069886', (15, 'WDS'): '3405,779024', (16, 'WDS'): '2042,401477', (20, 'WDS'): '284,5119135', (21, 'WDS'): '605,7323486', (22, 'WDS'): '7324,498321', (24, 'WDS'): '3749,602426', (25, 'WDS'): '4262,913102', (27, 'WDS'): '5568,744156', (28, 'WDS'): '2746,902945', (29, 'WDS'): '1808,746963', (30, 'WDS'): '1838,621175', (32, 'WDS'): '5991,470312', (33, 'WDS'): '8242,540054', (34, 'WDS'): '580,7872619', (35, 'WDS'): '3342,460004', (36, 'WDS'): '4148,466617', (37, 'WDS'): '1380,173565', (38, 'WDS'): '1028,567049', (40, 'WDS'): '795,446064', (41, 'WDS'): '4861,384368', (42, 'WDS'): '1701,227193', (43, 'WDS'):


pds_csv_with_multi = pds_csv.set_index(['ClusterId','WDS','ELEC'])
print(pds_csv_with_multi)
#pds_csv_with_multi.drop(index=('11219,11949', '12569,86931'), level=1,  inplace=True)
#print(pds_csv_with_multi.loc[2])

ind = pds_csv_with_multi.index[(pds_csv_with_multi['ED']=='1637,105397') & (pds_csv_with_multi['PNC']=='403,7666044')].tolist()
print("Found this" , ind)
pds_csv_with_multi.drop(index=ind, inplace=True)
print(pds_csv_with_multi)