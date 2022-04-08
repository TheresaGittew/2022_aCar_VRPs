
import fpvrp_GRBModel_XL as fpvrps
import fpvrp_PostProcessing as postprocessor
from fpvrp_RouteVizualizer import PVRP_Vizualizer
from fpvrp_ParameterInputClasses import InputGISReader, Scenario
from input_interface import DummyForExcelInterface_ET, DummyForExcelInterface_IC
from ExcelHandler import IOExcel
import random
from itertools import cycle


def optimize_scenario(scenario, framework_input, io_excel):
    model = fpvrps.FPVRPSVehInd(framework_input, scenario)
    model.set_constraints()
    model.set_objective()
    model.solve_model()
    io_excel.save_gurobi_res_in_excel\
            ([model.z, model.y, model.q, model.u], model.mp.objVal )

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
    io_excel_processed_results.save_df_res_in_excel([grb_results_unchanged['Z'], df_y_enhanced_without_multiindex, grb_results_unchanged['Q'], grb_results_unchanged['U']],
                                  new_total_costs)


def vizualize_results(scenario, framework_input, io_excel, root_directory_savings):
    grb_results_in_pd_dfs = io_excel.get_results_from_excel_to_df(with_multiindex=True)

    vizualizer = PVRP_Vizualizer(framework_input, scenario, grb_results_in_pd_dfs, root_directory_savings)
    #vizualizer.plot_routes()
    vizualizer.plot_active_cust()


# #
# constructing basic input objects (input_gis info; scenario info; general "paramter" info)
input_data_case = DummyForExcelInterface_ET().get_vehiclecapa_numdays_S() # to be replaced by class which extracts from excel file
input_gis = InputGISReader(input_data_case.daily_demand_factors[0], input_data_case.functions_to_consumption_per_T,
                           relative_path_to_demand='/GIS_Data/ET_Location_Data_WDS_ELEC_PNC.csv',
                           relative_path_to_coors='/GIS_Data/ET_Coordinates.csv',
                           relative_path_to_od_matrix='/GIS_Data/ET_ODs.csv', services=input_data_case.S) # important: stick to order in .csv!

total_demand = sum([value for key,value in input_gis.get_total_demands().items() if key[1] == 'ELEC'])
#print(total_demand)
#
scenario = Scenario(20, lower_bound=0, upper_bound=300, GIS_inputs=input_gis)
relevant_customers = len(scenario.C) / len(input_gis.get_customers())
#
#
framework_input = fpvrps.FPVRPVecIndConfg(input_data_case.T, W_i = input_gis.get_total_demands(),
                                          w_i= input_gis.get_daily_demands(), c =input_gis.get_od_to_dist(),
                                          coordinates=input_gis.get_coors(), S=input_data_case.S, H=input_data_case.H, travel_time=input_gis.get_od_to_time(),
                                          Q_h_s=input_data_case.Q_h_s, fixed_costs_h=input_data_case.fixed_costs, service_time=input_data_case.service_times)

#print(input_gis.get_total_demands())
#
io_excel = IOExcel(scenario, root_directory='04-08-CaseStudy', add_to_folder_title='', title_excel_to_create_or_read="DecisionvariableValues.xlsx",
                     titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
                                           ['Customer', 'Vehicle', 'Day', 'ServiceType'],['ConfigType','Vehicle']), output_tab_names=('Z', 'Y', 'Q','U'))
# #
optimize_scenario(scenario, framework_input, io_excel)
#
# # # post processing
excel_for_processed_data = IOExcel(scenario, root_directory='04-08-CaseStudy', add_to_folder_title='_', title_excel_to_create_or_read="DecisionvariableValues_PP.xlsx",
                     titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
                                           ['Customer', 'Vehicle', 'Day', 'ServiceType'],['ConfigType','Vehicle']), output_tab_names=('Z', 'Y', 'Q','U'))

#
postprocess_grb_results(scenario, framework_input, io_excel, excel_for_processed_data, input_gis)
# #
vizualize_results(scenario, framework_input, io_excel, io_excel.get_path_str_for_scenario())
#


