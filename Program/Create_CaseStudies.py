#[c for c in GIS_inputs.get_customers() if GIS_inputs.get_od_to_dist()[100, c] > lower_bound and GIS_inputs.get_od_to_dist()[100, c] < upper_bound]
from input_interface import  DummyForExcelInterface
import numpy as np
from fpvrp_ParameterInputClasses import InputGISReader
from Execute import execute_scenario
import random

slice= [37, 9, 30, 35, 27, 52, 41, 51, 45, 16, 13, 29, 40, 36, 4]

# enter number as run_type between 0 and 7 for specifying the specific case study (customer 'fragment')
class CaseStudy_INPUT():
    def __init__(self, run_type, case_study_type='ET', slice=None, root_directory= '04_14_CaseStudy', customer_fragment=((0, 40), (40, 60), (60, 70), (70, 80),
                                                                          (80, 85), (85, 90), (90, 95), (95, 100))):
        self.separate_runs = customer_fragment
        self.root_directory = root_directory+'_'+case_study_type+'_'+str(run_type)+'/'
        if slice:
            self.root_directory = root_directory+'_Slice_'+case_study_type+'_'+str(run_type)+'/'
        if case_study_type == 'ET':
            self.service_combis = iter([['WDS'], ['PNC'], ['ELEC'], ['ED'], ['WDS', 'PNC'],
                                   ['WDS', 'ELEC'], ['WDS', 'ED'], ['PNC', 'ELEC'],
                                   ['PNC', 'ED'], ['ELEC', 'ED'], ['WDS', 'PNC', 'ELEC'],
                                   ['WDS', 'PNC', 'ED'], ['WDS', 'ELEC', 'ED'], ['PNC', 'ELEC', 'ED'],
                                   ['WDS', 'PNC', 'ELEC', 'ED']])
            self.relative_path_to_demand = '/GIS_Data/ET_Location_Data.csv'
            self.relative_path_to_coors = '/GIS_Data/ET_Coordinates.csv'
            self.relative_path_to_od_matrix = '/GIS_Data/ET_ODs.csv'
        else:
            self.service_combis = iter([['PNC'], ['ELEC'], ['PNC', 'ELEC']])
            self.relative_path_to_demand = '/GIS_Data/IC_Location_Data.csv'
            self.relative_path_to_coors = '/GIS_Data/IC_Coordinates.csv'
            self.relative_path_to_od_matrix = '/GIS_Data/IC_ODs.csv'

        set_provided_services = next(self.service_combis, None)  # next_service_scen ist z.B. ['PNC','ED']
        lower_bound_ringarea = customer_fragment[run_type][0] / 100
        upper_bound_ringarea = customer_fragment[run_type][1] / 100

        # step 1: go through all service combinations
        while set_provided_services:
            input_interface = DummyForExcelInterface(set_provided_services).get_vehiclecapa_numdays_S()
            input_gis = InputGISReader(input_interface.daily_demand_factors[0],
                                       input_interface.functions_to_consumption_per_T,
                                       relative_path_to_demand=self.relative_path_to_demand,
                                       relative_path_to_coors=self.relative_path_to_coors,
                                       relative_path_to_od_matrix=self.relative_path_to_od_matrix,
                                       services=set_provided_services)

            # 2. Customer Scenarios
            distance_limits, customer_groups_shuffled = generate_relevant_customers(input_gis) if not slice else generate_relevant_customers(input_gis, slice)
            customer_scen_id_to_customer_list, customer_scen_id_to_coverage = create_customer_sets(distance_limits,
                                                                                                   customer_groups_shuffled,
                                                                                                   len(input_gis.customers)) if not slice else create_customer_sets(distance_limits,
                                                                                                   customer_groups_shuffled, len(slice))
            for customer_scenario_id, customer_lis in customer_scen_id_to_customer_list.items():
                percentage = customer_scen_id_to_coverage[customer_scenario_id]
                if percentage > lower_bound_ringarea and percentage <= upper_bound_ringarea:
                    print("RUN + + Scenario services: ", set_provided_services, " | S-Points : ", customer_lis,
                          " % Points (from tot. Area) ",  percentage, " | Customer Id : ", customer_scenario_id)
                    print("Used Capacities vehicle configs: ", input_interface.Q_h_s)
                    number_vehicles = len(customer_lis) * 30
                    execute_scenario(relevant_customers=customer_lis, number_vehicles=number_vehicles,
                                     input_interface=input_interface,
                                     input_gis=input_gis, root_directory=self.root_directory,
                                     customer_scenario=customer_scenario_id, services_scenario=set_provided_services)

            set_provided_services = next(self.service_combis, None)





index_hub = 100

# sukkzesives Hinzufügen von customers
def generate_relevant_customers(input_gis, slice=None):
    distance_categories = []
    max_distance_to_hub_ceil = np.ceil(max(input_gis.get_od_to_dist()[100, c] for c in input_gis.get_customers()))

    max_count = 30  # big number
    number_intervals = 6
    step_size = max_distance_to_hub_ceil / number_intervals

    # Distance limits
    distance_limits = [l * step_size for l in range(max_count) if (l* step_size) < max_distance_to_hub_ceil + 1]
    # print(distance_limits) # i.e. [0.0, 17.5, 35.0, 52.5, 70.0, 87.5, 105.0]

    # Create "groups" per distance category, the distance limit is the upper bound per category
    customer_groups = {}
    for i in range(len(distance_limits) - 1):
        distance_lb = distance_limits[i]
        distance_ub = distance_limits[i+1]
        if not slice:
            relevant_customers_current_distance_group = [c for c in input_gis.get_customers() if input_gis.get_od_to_dist()[100, c]
                 > distance_lb and input_gis.get_od_to_dist()[100, c] < distance_ub]
        else:
            relevant_customers_current_distance_group = [c for c in input_gis.get_customers() if
                                                         input_gis.get_od_to_dist()[100, c]
                                                         > distance_lb and input_gis.get_od_to_dist()[
                                                             100, c] < distance_ub and c in slice]
        customer_groups[distance_limits[i+1]] = relevant_customers_current_distance_group

    customer_groups_shuffled = {}
    for k, v in customer_groups.items():
        customerlist_copy = v.copy()
        random.seed(5)
        random.shuffle(customerlist_copy)
        customer_groups_shuffled[k] = customerlist_copy
    return distance_limits, customer_groups_shuffled


def create_customer_sets(distance_limits, customer_groups_shuffled, total_numb_customer):
    distance_limits_copy = distance_limits.copy()
    distance_limits_copy.reverse() #  returns for example [65.0, 54.166, 43.33, 32.5, 21.68, 10.83333, 0.0]
    customer_scenarios = []

    for current_distance_ub in distance_limits_copy[:-1]: # takes 65. first, then 54, then 43 ....
        customers_for_this_distance_category = iter(customer_groups_shuffled[current_distance_ub])
        next_customer = next(customers_for_this_distance_category, None)
        while next_customer:
            customer_scenarios = customer_scenarios + [customer_scenarios[-1] + [next_customer]] if customer_scenarios else [[next_customer]]
            next_customer = next(customers_for_this_distance_category, None)

    customer_scen_id_to_customer_list = {}
    for i in range(len(customer_scenarios)):
        customer_scen_id_to_customer_list[i] = customer_scenarios[i]

    customer_scen_id_to_coverage = {}
    for i in range(len(customer_scenarios)):
        customer_scen_id_to_coverage[i] = len(customer_scenarios[i]) / total_numb_customer

    return customer_scen_id_to_customer_list, customer_scen_id_to_coverage

# 8 parallel scenarios, each of them defined by lb and ub

# Dran denken! Wenn slice gewählt, neues root directory angeben
# c = CaseStudy_INPUT(0)





# relevant_customers = [2, 543, 43, 43, 3]
# num_vecs = 40 # wie hier upper bound herausfinden?
