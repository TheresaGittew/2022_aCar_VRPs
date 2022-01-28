import PVRP_Preprocessing as pv
import DEPR_ReadNilsInputFiles as dp
import PVRP_Formulation as optimizer

import SETUP_and_IO as stp
import PVRP_RouteVizualizer as vizualizer
import PVRPS_Formulation as optimizer_s

start_directory = '/home/sshrene/theresa/2022_aCar_VRPs'

# test_path =
# test_ cust

path_demand_file = start_directory + '/GIS_Data/22-01-04_DEMANDS_7_DAYS.csv' # '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/11-19-21_EXAMPLE_DemandList2.csv' # '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/01-01-03_DemandList.csv' #/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/11-19-21_EXAMPLE_DemandList2.csv'
path_OD_matrix = start_directory + '/GIS_Data/11-15-21_ODs.csv'
coordinates = dp.read_coors(start_directory + '/GIS_Data/11-15-21_CoordinatesLongitudeLatitude.csv')
#loc_excel_settings_description = '/Users/theresawettig/Dropbox/aCar/12-2_Input_Optimizer.xlsx'

od_matrix_as_dict = dp.read_odmatrix(path_OD_matrix)
od_matrix_with_distances = dict((k, od_matrix_as_dict[k][1]) for k in od_matrix_as_dict.keys())

capa_for_vrps = {(0, 'PNC'): 30, (0, 'WDS'): 300, (1, 'PNC'): 30, (1, 'WDS'): 300, (2, 'PNC'): 30, (2, 'WDS'): 300, (3, 'PNC'): 20, (3, 'WDS'): 600, (4, 'PNC'): 20, (4, 'WDS'): 600, (5, 'PNC'): 20, (5, 'WDS'): 600, (6, 'PNC'): 30, (6, 'WDS'): 500, (7, 'PNC'): 30, (7, 'WDS'): 500}  # TODO start here again
capa = 25
num_days = 6

# scenario dependent data
distances_lbs = 25
distances_ubs = 100
number_vehicles = 3
relevant_customers = dp.find_relevant_customers(od_matrix_as_dict, number_customers=25, min_distance_bekoji=distances_lbs, max_distance_bekoji=distances_ubs) #  [1,4,6,9,10,17,18,22]todo: improve method and overall procedure  #
print("ACTIVE CUSTOMERS : " , relevant_customers)
scenarios = [pv.Scenario(number_vehicles, distances_lbs, distances_ubs, relevant_customers)] # list of scenarios to analyze

# #- - - - - -  ONLY PREPROCESSING - - - - - - - - -
for next_scenario in scenarios:

    # initialize input data
    T = [i for i in range(num_days)]
    od_matrix_as_dict = dp.read_odmatrix(path_OD_matrix)
    od_matrix_with_distances = dict((k, od_matrix_as_dict[k][1]) for k in od_matrix_as_dict.keys())

    arcs = od_matrix_as_dict.keys()
    total_demands_nested_dict, daily_max_demand_nested_dict = dp.read_demands(path_demand_file, demand_type_names=['PNC','WDS'])
    print(total_demands_nested_dict)
    R, R_lengths = pv.find_all_routes(next_scenario.C, od_matrix_with_distances)
    P = pv.create_all_schedules(len(T))
    demand_per_schedule = pv.find_demand_per_schedule(P,  next_scenario.C, total_demands_nested_dict)

    stp.create_directory_for_scenario(next_scenario, root_directory='Results_PVRPS')
    C_p = pv.find_schedules_for_each_customer(list(P.keys()),relevant_customers )
    C_ps = pv.find_schedules_for_each_customer_and_service(list(P.keys()),relevant_customers, ['PNC', 'WDS'])
    stp.save_preprocessing_results_in_csv(R, P, C_p, C_ps, demand_per_schedule, next_scenario, root_directory='Results_PVRPS') # TOdo: change root directory



# - - - - - - - AFTER PREPROCESSING - - - - - - - - - - -
# #
for next_scenario in scenarios:
    R, P, unnütz = stp.get_preprocessing_results_from_csv(next_scenario, root_directory='Results_PVRPS')

    N = [0] + next_scenario.C
    T = [i for i in range(num_days)]
    od_matrix_as_dict = dp.read_odmatrix(path_OD_matrix)
    od_matrix_with_distances = dict((k, od_matrix_as_dict[k][1]) for k in od_matrix_as_dict.keys())

    total_demands_nested_dict, daily_max_demand_nested_dict = dp.read_demands(path_demand_file, demand_type_names=['PNC', 'WDS'])

    a = pv.create_a_param(R,  next_scenario.C)
    b = pv.create_b_p_t(P, T)
    demand_per_schedule = pv.find_demand_per_schedule(P,  next_scenario.C, total_demands_nested_dict)
    C_p = pv.find_schedules_for_each_customer(list(P.keys()), next_scenario.C)
    C_ps = pv.find_schedules_for_each_customer_and_service(list(P.keys()),relevant_customers, ['PNC', 'WDS'])
    E_r = pv.create_e_r(R)

    # additionally neede
    demand = total_demands_nested_dict
    input = pv.Config_Input_PVRP(R, T, P, C_ps, a, b, demand_per_schedule, capa_for_vrps, E_r, od_matrix_with_distances, coordinates, ['PNC', 'WDS'])

    model = optimizer_s.PVRPS_Formulation(input, next_scenario)
    model.set_constraints()
    model.set_objective()
    model.solve_model()
    stp.save_gurobi_res_in_excel_with_services(model, next_scenario, root_directory='Results_PVRPS') # change this method


    ##
    # paint outputs
    path_results = stp.create_directory_for_scenario(next_scenario)



    vizualizer = vizualizer.PVRP_Vizualizer(path_preprocessing=stp.get_path_for_scenario_preprocessing_file(next_scenario, 'Preprocessing_Inputs.xlsx','Results_PVRPS'),
                                            path_results_grb=stp.get_path_for_scenario_results_file(next_scenario, name_file='DecisionvariableValues.xlsx', root_directory='Results_PVRPS'), root_directory_for_saving='Results_PVRPS', gurobi_model=model)
    vizualizer.plot_routes(method_for_getting_routes=vizualizer.get_next_day_routes_from_h)



#
#
#
#
#
# #
# #
# #
