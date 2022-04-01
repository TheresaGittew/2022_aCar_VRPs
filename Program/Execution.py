import fpvrp_GRBModel_XL as fpvrps
import fpvrp_PostProcessing as postprocessor
from fpvrp_RouteVizualizer import PVRP_Vizualizer
from fpvrp_ParameterInputClasses import InputGISReader, Scenario, DummyForExcelInterface
from ExcelHandler import IOExcel
import random
from itertools import cycle


def optimize_scenario(scenario, framework_input, io_excel, with_battery=False):
    model = fpvrps.FPVRPSVehInd(framework_input, scenario, with_battery)
    model.set_constraints()
    model.set_objective()
    model.solve_model()
    if not with_battery:
        io_excel.save_gurobi_res_in_excel\
            ([model.z, model.y, model.q], model.mp.objVal )
    else:
        io_excel.save_gurobi_res_in_excel \
            ([model.z, model.y, model.q, model.l, model.battery, model.full_rng_for_l], model.mp.objVal)

def postprocess_grb_results( scenario, framework_input, io_excel_grb_results, io_excel_processed_results, input_gis):
    grb_results_in_pd_dfs = io_excel_grb_results.get_results_from_excel_to_df(with_multiindex=True)
    grb_objVal = io_excel_grb_results.get_obj_val_from_excel()

    # #
    # adjust dataframe y (used links)
    pp = postprocessor.FPVRPPostProcessor(framework_input, scenario, grb_results_in_pd_dfs, input_gis.get_od_to_dist())
    df_y_corrected_without_multiindex = pp.correct_routes(grb_results_in_pd_dfs['Y'])
    additional_costs = pp.get_distance()


    # #
    #
    df_y_enhanced_without_multiindex = pp.enhance_routes(pp.set_multiindex_for_y_df(df_y_corrected_without_multiindex))
    # print(df_y_enhanced_without_multiindex)
    cost_savings = pp.get_distance()

    new_total_costs = grb_objVal + additional_costs + cost_savings
    print("New total costs: " , new_total_costs, " - - Grb Obj Val: ", grb_objVal, " | add. cost: ", additional_costs, " | savings 2opt: ", cost_savings)


    grb_results_unchanged = io_excel_grb_results.get_results_from_excel_to_df(with_multiindex=False)
    io_excel_processed_results.save_df_res_in_excel([grb_results_unchanged['Z'], df_y_enhanced_without_multiindex, grb_results_unchanged['Q']],
                                  new_total_costs)


def vizualize_results(scenario, framework_input, io_excel, root_directory_savings):
    grb_results_in_pd_dfs = io_excel.get_results_from_excel_to_df(with_multiindex=True)

    vizualizer = PVRP_Vizualizer(framework_input, scenario, grb_results_in_pd_dfs, root_directory_savings)
    #vizualizer.plot_routes()
    vizualizer.plot_active_cust()


# #
# constructing basic input objects (input_gis info; scenario info; general "paramter" info)
vehicle_capa, T, S = DummyForExcelInterface().get_vehiclecapa_numdays_S() # to be replaced by class which extracts from excel file

input_gis = InputGISReader(relative_path_to_demand='/GIS_Data/ET_Location_Data.csv',
                           relative_path_to_coors='/GIS_Data/ET_Coordinates.csv',
                           relative_path_to_od_matrix='/GIS_Data/ET_ODs.csv', services=S) # important: stick to order in .csv!
scenario = Scenario(10, lower_bound=0, upper_bound=300, GIS_inputs=input_gis)
#relevant_customers = len(scenario.C) / len(input_gis.get_customers())



print("SUM " , sum(input_gis.get_total_demands()[i, 'WDS'] for i in scenario.C))
print("SUM PNC " , sum(input_gis.get_total_demands()[i, 'PNC'] for i in scenario.C))
#
framework_input = fpvrps.FPVRPVecIndConfg(T,  W_i = input_gis.get_total_demands(),
                                           w_i= input_gis.get_daily_demands(), capa=vehicle_capa, c =input_gis.get_od_to_dist(),
                                           coordinates=input_gis.get_coors(), S=S, travel_time=input_gis.get_od_to_time())
#
# io_excel_withbattery = IOExcel(scenario, root_directory='03-08-Results_FP-VRPs', add_to_folder_title='_Battery', title_excel_to_create_or_read="DecisionvariableValues.xlsx",
#                     titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
#                                            ['Customer', 'Vehicle', 'Day', 'ServiceType'], ['O','D','Vehicle','Day','Servicetype'], ['Node', 'Vehicle', 'Day'], ['Node', 'Vehicle', 'Day']), output_tab_names=('Z', 'Y', 'Q','L','Battery','Range'))
io_excel = IOExcel(scenario, root_directory='03-30-Results_FP-VRPs_XL', add_to_folder_title='_WDS', title_excel_to_create_or_read="DecisionvariableValues.xlsx",
                     titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
                                           ['Customer', 'Vehicle', 'Day', 'ServiceType'], ['O','D','Vehicle','Day','Servicetype']), output_tab_names=('Z', 'Y', 'Q'))
# #
optimize_scenario(scenario, framework_input, io_excel, with_battery=False)

# # post processing
excel_for_processed_data = IOExcel(scenario, root_directory='03-24-Results_FP-VRPs_XL', add_to_folder_title='_WDS', title_excel_to_create_or_read="DecisionvariableValues_PP.xlsx")
postprocess_grb_results(scenario, framework_input, io_excel, excel_for_processed_data, input_gis)
#
vizualize_results(scenario, framework_input, io_excel, io_excel.get_path_str_for_scenario())



