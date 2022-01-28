import PVRP_Preprocessing as pv
import DEPR_ReadNilsInputFiles as dp
import FPVRPS_VehicleIndex as optimizer
import SETUP_and_IO as stp
import ScenarioClass as sc_definer

test_file = '/GIS_Data/11-19-21_EXAMPLE_DemandList2.csv'
start_directory = '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs'  # '/home/sshrene/theresa/2022_aCar_VRPs'
path_demand_file = start_directory + '/GIS_Data/22-01-04_DEMANDS_7_DAYS.csv' #  '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/11-19-21_EXAMPLE_DemandList2.csv' # start_directory + '/GIS_Data/22-01-04_DEMANDS_7_DAYS.csv' # '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/11-19-21_EXAMPLE_DemandList2.csv' # '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/01-01-03_DemandList.csv' #/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/GIS_Data/11-19-21_EXAMPLE_DemandList2.csv'
path_OD_matrix = start_directory + '/GIS_Data/11-15-21_ODs.csv'
coordinates = dp.read_coors(start_directory + '/GIS_Data/11-15-21_CoordinatesLongitudeLatitude.csv')
od_matrix_as_dict = dp.read_odmatrix(path_OD_matrix)
od_matrix_with_distances = dict((k, od_matrix_as_dict[k][1]) for k in od_matrix_as_dict.keys())

capa_for_vrps = {(0, 'PNC'): 0, (0, 'WDS'): 600, (1, 'PNC'): 0, (1, 'WDS'): 600, (2, 'PNC'): 0, (2, 'WDS'): 600, (3, 'PNC'): 20, (3, 'WDS'): 600, (4, 'PNC'): 20, (4, 'WDS'): 600, (5, 'PNC'): 20, (5, 'WDS'): 600, (6, 'PNC'): 30, (6, 'WDS'): 500, (7, 'PNC'): 30, (7, 'WDS'): 500}  # TODO start here again
capa = 25
num_days = 5

# scenario dependent data
distances_lbs = 5
distances_ubs = 120
number_vehicles = 7
relevant_customers = dp.find_relevant_customers(od_matrix_as_dict, number_customers=25, min_distance_bekoji=distances_lbs, max_distance_bekoji=distances_ubs) #  [1,4,6,9,10,17,18,22]todo: improve method and overall procedure  #
print("ACTIVE CUSTOMERS : " , relevant_customers)
scenarios = [sc_definer.Scenario(number_vehicles, distances_lbs, distances_ubs, relevant_customers, num_days)] # list of scenarios to analyze
S = ['PNC', 'WDS']

# #- - - - - -  ONLY PREPROCESSING - - - - - - - - -

for next_scenario in scenarios:

    T = [i for i in range(num_days)]
    od_matrix_as_dict = dp.read_odmatrix(path_OD_matrix)
    od_matrix_with_distances = dict((k, od_matrix_as_dict[k][1]) for k in od_matrix_as_dict.keys())

    total_demands_nested_dict, daily_max_demand_nested_dict = dp.read_demands(path_demand_file, demand_type_names=['PNC', 'WDS'])
    A = list(od_matrix_with_distances.keys())

    # get subsets for subtour elim constraint
    # preprocesser = fpvrp_vi.FPVRPVecIndPreProcess(relevant_customers , A)
    # subset_id_to_A = preprocesser.get_subset_id_to_A()
    # subset_id_to_C = preprocesser.get_subset_id_to_C()

    input = optimizer.FPVRPVecIndConfg(T, A, total_demands_nested_dict, daily_max_demand_nested_dict, capa_for_vrps, od_matrix_with_distances, coordinates, S,0,0,0)

    model = optimizer.FPVRPSVehInd(input, next_scenario)
    model.set_constraints()
    model.set_objective()
    model.solve_model()

    stp.save_gurobi_res_in_excel_fpvrp([model.z, model.y, model.q], model.fpvrp_obj.objVal, next_scenario, path='../Results_FPVRPS') # change this method

    ##
    # paint outputs
   # path_results = stp.create_directory_for_scenario(next_scenario)



    ##vizualizer = vizualizer.PVRP_Vizualizer(path_preprocessing=stp.get_path_for_scenario_preprocessing_file(next_scenario, 'Preprocessing_Inputs.xlsx','Results_PVRPS'),
    #                                       path_results=stp.get_path_for_scenario_results_file(next_scenario, name_file='DecisionvariableValues.xlsx', root_directory='Results_PVRPS'), root_directory_for_saving='Results_PVRPS', pvrp_model=model)
    #vizualizer.plot_routes(method_for_getting_routes=vizualizer.get_next_day_routes_from_h)

