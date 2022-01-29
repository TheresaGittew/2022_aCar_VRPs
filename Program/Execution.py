import fpvrp_GRBModel as fpvrps
import fpvrp_PostProcessing as postprocessor
from fpvrp_RouteVizualizer import PVRP_Vizualizer
from fpvrp_ParameterInputClasses import InputGISReader, Scenario, DummyForExcelInterface
from ExcelHandler import IOExcel


def optimize_scenario(scenario, framework_input, io_excel):
    model = fpvrps.FPVRPSVehInd(framework_input, scenario, True)
    model.set_constraints()
    model.set_objective()
    model.solve_model()
    io_excel.save_gurobi_res_in_excel\
        ([model.z, model.y, model.q, model.l, model.battery, model.full_rng_for_l], model.mp.objVal )


def postprocess_grb_results( scenario, framework_input, io_excel_grb_results, io_excel_processed_results):
    grb_results_in_pd_dfs = io_excel_grb_results.get_results_from_excel_to_df(with_multiindex=True)
    grb_objVal = io_excel_grb_results.get_obj_val_from_excel()

    pp = postprocessor.FPVRPPostProcessor(framework_input, scenario, grb_results_in_pd_dfs)
    pp.correct_routes(input_gis.get_od_to_dist())

    df_y_res_with_multiindex = pp.get_df_y_with_multiindex()  # diese methoden nochmal umbenennen; wichtig, dass die heir nicht grundsätzlich erstellt werden sondern es sich um manipulierte ergebnisse handelt
    df_grb_res_adjusted = pp.get_dfs_without_multiindex()
    new_costs = pp.get_distance()

    new_total_costs = grb_objVal + new_costs
    io_excel_processed_results.save_df_res_in_excel([df_grb_res_adjusted['Z'], df_grb_res_adjusted['Y'], df_grb_res_adjusted['Q']],
                                  new_total_costs)


def vizualize_results(scenario, framework_input, io_excel, root_directory_savings):
    grb_results_in_pd_dfs = io_excel.get_results_from_excel_to_df(with_multiindex=True)

    vizualizer = PVRP_Vizualizer(framework_input, scenario, grb_results_in_pd_dfs, root_directory_savings)
    vizualizer.plot_routes()
    vizualizer.plot_active_cust()


# #
# constructing basic input objects (input_gis info; scenario info; general "paramter" info)
vehicle_capa, T, S = DummyForExcelInterface().get_vehiclecapa_numdays_S() # to be replaced by class which extracts from excel file

input_gis = InputGISReader(relative_path_to_demand='/GIS_Data/ET_Location_Data.csv',
                           relative_path_to_coors='/GIS_Data/ET_Coordinates.csv',
                           relative_path_to_od_matrix='/GIS_Data/ET_ODs.csv', services=S) # important: stick to order in .csv!
scenario = Scenario(3, lower_bound=51, upper_bound=80, GIS_inputs=input_gis)
print("SUM " , sum(input_gis.get_total_demands()[i, 'WDS'] for i in scenario.C))
print("SUM " , sum(input_gis.get_total_demands()[i, 'PNC'] for i in scenario.C))

framework_input = fpvrps.FPVRPVecIndConfg(T, A=list(input_gis.get_od_to_dist().keys()), W_i = input_gis.get_total_demands(),
                                          w_i= input_gis.get_daily_demands(), capa=vehicle_capa, c =input_gis.get_od_to_dist(),
                                          coordinates=input_gis.get_coors(), S=S)

io_excel = IOExcel(scenario, root_directory='01-28-Results_FP-VRPs', add_to_folder_title='_Test', title_excel_to_create_or_read="DecisionvariableValues.xlsx",
                   titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
                                          ['Customer', 'Vehicle', 'Day', 'ServiceType'], ['O','D','Vehicle','Day','Servicetype'], ['Node', 'Vehicle', 'Day'], ['Node', 'Vehicle', 'Day']), output_tab_names=('Z', 'Y', 'Q','L','battery','fullrange'))
optimize_scenario(scenario, framework_input, io_excel)

# # post processing
io_excel_for_processed_data = IOExcel(scenario, root_directory='01-27-Results_FP-VRPs', add_to_folder_title='_Test', title_excel_to_create_or_read="DecisionvariableValues_PP.xlsx")
#postprocess_grb_results( scenario, framework_input, io_excel, io_excel_for_processed_data)
#
#vizualize_results(scenario, framework_input, io_excel, '01-27-Results_FP-VRPs')


