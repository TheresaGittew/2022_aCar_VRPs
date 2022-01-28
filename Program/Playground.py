from Program.Deprecated import DEPR_ReadNilsInputFiles as dp, SETUP_and_IO as setio

A = ['Ernie', 'Bert', 'Bibo']
B = ['green', 'yellow', 'blue']
C = [4,8, 14]
path_demand_file = '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/11-19-21_EXAMPLE_DemandList2.csv'
path_results = 'Results/Scenario_NumVec2-LBs35-UBs80/DecisionvariableValues.xlsx'


total_demands_nested_dict, daily_max_demand_nested_dict = dp.read_demands(path_demand_file,
                                                                              demand_type_names=['PNC', 'WDS'])
print(total_demands_nested_dict)

print(sum(list(map(lambda x: x['PNC'],list(total_demands_nested_dict.values())))))
print(185 / 8)

pd_x = setio.get_x_df(path_results)

res = list(pd_x.query('Day == ' + str(2))['RouteId'])
print(res)


self.fpvrp_obj.setObjective(
            sum(sum(sum(self.x[r, t] * self.cfg.c[i, j] for (i, j) in self.cfg.E_r[r]) for r in self.cfg.R_ids) for t in self.cfg.T))

1368

