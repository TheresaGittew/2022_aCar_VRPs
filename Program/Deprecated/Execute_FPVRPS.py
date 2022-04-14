import FPVRPS_VehicleIndex as fpvrps
import SETUP_and_IO as stp
import FPVRP_PostProcessing as postprocessor
import FPVRPS_RouteVizualizer as vizualizer
from FPVRP_Inputs import InputGISReader, Scenario, DummyForExcelInterface

# #
# reading of input data
vehicle_capa, T, S = DummyForExcelInterface().get_vehiclecapa_numdays_S() # to be replaced by class which extracts from excel file
print(S)
input_gis = InputGISReader(relative_path_to_demand='/GIS_Data/22-01-04_DEMANDS_7_DAYS.csv',
                           relative_path_to_test_demand='/GIS_Data/11-19-21_EXAMPLE_DemandList2.csv',
                           relative_path_to_coors='/GIS_Data/11-15-21_CoordinatesLongitudeLatitude.csv',
                           relative_path_to_od_matrix='/GIS_Data/11-15-21_ODs.csv', services=S) # important: stick to order in .csv!

# encapsulating info into object scenario and input (for all scenario independent data)
scenario = Scenario(5, lower_bound=20, upper_bound=83, GIS_inputs=input_gis)
print("relevant Customers: " , scenario.C , " share : ", (len(scenario.C) / 25))
print("total demand WDS: ", sum(input_gis.total_demands_nested_dict[i]['WDS'] for i in scenario.C))
print("total demand PNC: ", sum(input_gis.total_demands_nested_dict[i]['PNC'] for i in scenario.C))

framework_input = fpvrps.FPVRPVecIndConfg(T, A=list(input_gis.get_od_to_dist().keys()), W_i = input_gis.get_total_demands(),
                                          w_i= input_gis.get_daily_max_demand_dict(), capa=vehicle_capa, c =input_gis.od_to_distance,
                                          coordinates=input_gis.coordinates, S=S)

model = fpvrps.VRP_VBS_Optimizer(framework_input, scenario)
model.set_constraints()
model.set_objective()
model.solve_model()
#
# # # #
# # # save the result after model run
# # # a new folder + excel file is created for the current scenario; we need to provide the root directory
stp.create_directory_for_scenario(scenario, root_directory='__Results_FP-VRPs')
relative_path_to_scenario = stp.get_path_str_for_scenario(scenario, root_directory='__Results_FP-VRPs')
stp.save_gurobi_res_in_excel_fpvrp([model.z, model.y, model.q], model.mp.objVal, relative_path_to_excel=relative_path_to_scenario+ "DecisionvariableValues.xlsx") # change this method
#
# #
# # # Post processing (route correction etc)
pp = postprocessor.FPVRPPostProcessor(relative_path_to_scenario + "DecisionvariableValues.xlsx", scenario, framework_input)
vehicle_day_to_arcs, additional_distance_after_adjust, o_d_vec_day = pp.correct_routes(input_gis.od_to_distance)
new_total_costs = model.mp.objVal + additional_distance_after_adjust
stp.save_gurobi_res_in_excel_fpvrp([model.z, o_d_vec_day, model.q], new_total_costs, relative_path_to_excel = relative_path_to_scenario + "DecisionvariableValues_PP.xlsx", from_gurobi=False)
#
# #
# Route Vizualization

vizualizer = vizualizer.PVRP_Vizualizer(relative_path_to_scenario + "DecisionvariableValues_PP.xlsx" , relative_path_to_scenario, model)

vizualizer.plot_routes()