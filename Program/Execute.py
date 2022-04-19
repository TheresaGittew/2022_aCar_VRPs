
import fpvrp_GRBModel_XL as fpvrps
import fpvrp_PostProcessing as postprocessor
from fpvrp_RouteVizualizer import PVRP_Vizualizer
from fpvrp_ParameterInputClasses import InputGISReader, Scenario
from input_interface import DummyForExcelInterface
from ExcelHandler import IOExcel
import random
from itertools import cycle



def sub_optimize_scenario(scenario, cfg_params, io_excel):
    model = fpvrps.VRP_VBS_Optimizer(cfg_params, scenario)
    model.set_constraints()
    model.set_objective()
    model.solve_model()
    io_excel.save_gurobi_res_in_excel\
            ([model.z, model.y, model.q, model.u], model.mp.objVal, model.mp.Runtime, model.mp.MIPGap)

def sub_postprocess_grb_results(scenario, framework_input, io_excel_grb_results, io_excel_processed_results, input_gis):
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
                                  new_total_costs, 0, 0)


def sub_vizualize_results(scenario, framework_input, io_excel, root_directory_savings):
    grb_results_in_pd_dfs = io_excel.get_results_from_excel_to_df(with_multiindex=True)

    vizualizer = PVRP_Vizualizer(framework_input, scenario, grb_results_in_pd_dfs, root_directory_savings)
    vizualizer.plot_routes()
    vizualizer.plot_active_cust()


# Ziel:
# Funktion, die aktuelles Szenario nimmt und übergreifend die input parameter hin und her schiebt u. Unterfunktionen aufruft
# u. letztlich Optimierung startet
def execute_scenario(relevant_customers, number_vehicles, input_interface, input_gis, root_directory,
                      services_scenario, customer_scenario, percentage, with_vizualization=True):

    scenario = Scenario(number_vehicles, GIS_inputs=input_gis, relevant_customers=relevant_customers)

    # #
    # just one slightly more clearer way to "save" parameters and safe them under the 'labels' of the model notation
    cfg_params = fpvrps.FPVRPVecIndConfg(input_interface.T, W_i = input_gis.get_total_demands(),
                                          w_i= input_gis.get_daily_demands(), c =input_gis.get_od_to_dist(),
                                          coordinates=input_gis.get_coors(), S=input_interface.S, H=input_interface.H,
                                          travel_time=input_gis.get_od_to_time(), Q_h_s=input_interface.Q_h_s,
                                          fixed_costs_h=input_interface.fixed_costs,
                                          service_time=input_interface.service_times)

    # #
    # Anlegen Excel-Objekt als Handler der Ergebnisse (ohne Nachbearbeitung)
    io_excel = IOExcel(scenario, root_directory=root_directory, scenario_id=''+str(services_scenario)+' '+str(customer_scenario) +' '+str(percentage), add_to_folder_title='',
                       title_excel_to_create_or_read="DecisionvariableValues.xlsx",
                       titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
                                                ['Customer', 'Vehicle', 'Day', 'ServiceType'],
                                                ['ConfigType', 'Vehicle']), output_tab_names=('Z', 'Y', 'Q', 'U'))

    sub_optimize_scenario(scenario, cfg_params, io_excel)

    io_excel_for_processed_data = IOExcel(scenario, root_directory=root_directory, scenario_id=''+str(services_scenario)
                                                                                               +' '+str(customer_scenario)
                                                                                               +' '+str(percentage),
                                       add_to_folder_title='', title_excel_to_create_or_read="DecisionvariableValues_PP.xlsx",
                                       titles_keys_per_dec_var=(
                                       ['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
                                       ['Customer', 'Vehicle', 'Day', 'ServiceType'], ['ConfigType', 'Vehicle']),
                                       output_tab_names=('Z', 'Y', 'Q', 'U'))

    sub_postprocess_grb_results(scenario, cfg_params, io_excel, io_excel_for_processed_data, input_gis)
    sub_vizualize_results(scenario, cfg_params, io_excel_for_processed_data,
                          io_excel_for_processed_data.get_path_str_for_scenario())


#
# input_data_case = DummyForExcelInterface_ET().get_vehiclecapa_numdays_S()  # infos über betrachtete services, kapazitäten, etc...
# relevant_customers = [2, 543, 43, 43, 3]
# num_vecs = 40 # wie hier upper bound herausfinden?



#print(input_gis.get_total_demands())
## todo: benennung anpassen
#
# # # post processing
#


