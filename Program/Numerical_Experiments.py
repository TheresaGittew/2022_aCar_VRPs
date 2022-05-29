import random
import numpy as np
from itertools import cycle, combinations
import itertools
from ExcelHandler import IOExcel
import fpvrp_GRBModel_XL as fpvrps
import os
import pandas
import statistics
import numpy
from Execute import sub_optimize_scenario

index_hub = 100

# #
# Some method specifically used for the numerical experiments as a part of the master thesis
# # Create a ScenarioCreator Object and call method "execute_all_scenarios()" to perform model runs for all defined
# scenario combinations
# Go to line ~240 to see how different parameter to study can be defined
# Then, run this file.


# Get root directory
def _get_root_directory():
    root_directory_program = os.path.dirname(
        os.path.abspath("README.md"))  # for example: /Users/theresawettig/PycharmProjects/2022_aCar_VRPs/Program
    return os.path.dirname(root_directory_program)

# #
# Generator of Vehicle-related Input Parameter for the numerical experiments
# For a given set of services (a number of services), and a specific option for the capacity sice (capa_size_opt),
# either 'L' or 'S', VehicleSettings() produces parameters configurations and related capacities. Usually
# automatically called from within the ScenarioCreator() class

class VehicleSettings():

    def __init__(self, num_services, capa_size_opt):

        self.capa_size = capa_size_opt
        self.services = [s for s in range(num_services)]

        # #
        # We predefine that there are usually 5 vehicle configurations to chose from for each combination

        if self.capa_size == 'L':
            self.max_capa = 60
        else:
            self.max_capa = 30

        # #
        # create all possible combinations of services from which vehicle configurations can be derived
        all_combis = []
        for len_combi in range(1, (num_services) + 1):
            res = list(itertools.combinations([i for i in range(num_services)], r=len_combi))
            print(res)
            all_combis = all_combis + res


        self.H = [i for i in range(len(all_combis))]
        services_per_combi = dict((i, len(all_combis[i])) for i in range(len(all_combis)))
        self.Q_h_s = {}

        combi_counter = 0
        for h in self.H:
            remaining_capa = self.max_capa
            self.Q_h_s[h] = {}
            for s in self.services:
                if s in all_combis[combi_counter]:
                    capa_for_current_service = self.max_capa / services_per_combi[h]
                    self.Q_h_s[h][s] = capa_for_current_service if capa_for_current_service <= remaining_capa else remaining_capa
                    remaining_capa = max(remaining_capa - capa_for_current_service, 0)
                else:
                    self.Q_h_s[h][s] = 0
            combi_counter += 1
        self.fixed_vehicle_costs = self._generate_vehicle_costs()

    def get_Q_h_s(self):
        return self.Q_h_s

    def get_H(self):
        return self.H

    def _generate_vehicle_costs(self):
        dict_config_to_costs = {}

        for h in self.H:
            num_services_current_config = 0
            for s in (self.services):
                num_services_current_config += 1 if self.Q_h_s[h][s] > 0 else 0
            dict_config_to_costs[h] = 10000 + 2000 * num_services_current_config
        return dict_config_to_costs

# #
# Generator of a Spatial Structure for the Numerical Study
# Specify num_customers (number customers), number services, cluster degree (between 0 and 2), demand level (demand_height),
# demand quantity option (homogen / heterogen), or w_i ('EQ_W','HALF_W) as a fraction of W_i to produce a
# specific Spatial structure
# Usually, that class is automatically called by class ScenarioCreator()

class SpacialStructure():

    def __init__(self, num_customers, num_services, cluster_degree_choice=0, demand_q_opt='HOMOGEN', demand_height='HIGH', w_i_choice=0, cluster_degree=(0,1,2),
                 w_i_options=('EQ_W', 'HALF_W'), with_fixed_seed=True):
        if with_fixed_seed: random.seed(42)
        self.num_customers = num_customers
        self.customers = [i for i in range(self.num_customers)]
        self.cluster_degree = cluster_degree[cluster_degree_choice]
        self.demand_quantities = demand_q_opt
        self.w_i_cfg = w_i_options[w_i_choice]
        self.num_services = num_services
        self.demand_height = demand_height

        self.coordinates_dict_x, self.coordinates_dict_y = self._create_nodes()
        self.dict_distance, self.dict_duration = self._create_matrix()
        self.dict_i_s_to_total_demand, self.mean, self.std = self._create_Wi()
        # print(self.dict_i_s_to_total_demand)
        self.dict_i_s_to_daily_demand = self._create_wi()


    def _create_Wi(self):
        print(self.demand_height)

        if self.demand_height == 'HIGH':
            self.demand_range_lb_hg = 50
            self.demand_range_ub_hg = 80
            self.demand_range_lb_htg = iter(cycle((25, 50, 75)))
            self.demand_range_ub_htg = iter(cycle((55, 80, 105)))

        if self.demand_height == 'LOW':
            self.demand_range_lb_hg = 30
            self.demand_range_ub_hg = 60
            self.demand_range_lb_htg = iter(cycle((5, 30, 55)))
            self.demand_range_ub_htg = iter(cycle((35, 60, 85)))

        dict_i_s_to_total_demand = {}
        if self.demand_quantities == 'HOMOGEN':
            dict_i_s_to_total_demand = dict (((i,s), random.randint(self.demand_range_lb_hg, self.demand_range_ub_hg)) for i in self.customers for s in range(self.num_services))
        else :
            for s in range(self.num_services):

                dict_i_s_to_total_demand = dict(((i, s), random.randint(next(self.demand_range_lb_htg), next(self.demand_range_ub_htg))) for i in self.customers
                                                for s in range(self.num_services))

        print("Demands:")
        for k,v in dict_i_s_to_total_demand.items():
            print("Key : " , k, " |value ",  v)

        mean_demand = statistics.mean(list(dict_i_s_to_total_demand.values()))
        mean_deviation = numpy.std(list(dict_i_s_to_total_demand.values()))
        print("mean demand" , mean_demand, " mean deviation : ", mean_deviation)
        return dict_i_s_to_total_demand, mean_demand, mean_deviation

    def _create_wi(self):
        dict_i_s_to_daily_demand = {}
        for s in range(self.num_services):
            for i in self.customers:
                dict_i_s_to_daily_demand[i, s] = self.dict_i_s_to_total_demand[i,s] \
                    if self.w_i_cfg == 'EQ_W' else np.floor(self.dict_i_s_to_total_demand[i,s] / 2)
        return dict_i_s_to_daily_demand

    def _euclidean_distance(self, i,j):
        x_distance = abs(self.coordinates_dict_x[i] - self.coordinates_dict_x[j])
        y_distance = abs(self.coordinates_dict_y[i] - self.coordinates_dict_y[j])
        return round(np.sqrt([x_distance ** 2 + y_distance ** 2])[0] * 40 ,2)

    def _create_matrix(self):
        tempo = 40  # km / h
        dict_distance = dict(((i, j), self._euclidean_distance(i, j)) for i in self.customers + [index_hub] for j in
            self.customers + [index_hub] if i != j)
        dict_duration = dict(((i, j), dict_distance[i, j] / tempo) for i in self.customers + [index_hub] for j in
            self.customers + [index_hub] if i != j)
        return dict_distance, dict_duration

    # print(self.dict_distance)
    def _create_nodes(self):
        self.x_coors_absolut_lb = 7.1
        self.x_coors_absolut_ub = 8.0
        self.y_coors_absolut_lb = 38.9
        self.y_coors_absolut_ub = 39.7

        dict_i_to_x_coor = {}
        dict_i_to_y_coor = {}

        ##
        # Add coordinates of hub
        dict_i_to_x_coor[100] = self.x_coors_absolut_lb + (self.x_coors_absolut_ub - self.x_coors_absolut_lb) / 2
        dict_i_to_y_coor[100] = self.y_coors_absolut_lb + (self.y_coors_absolut_ub - self.y_coors_absolut_lb) / 2

        ##
        # Create Coordinates according to clusters
        for i in range(self.num_customers):

            # #
            # x coordinate
            x_coor_width_for_cluster_degree = (self.x_coors_absolut_ub -  self.x_coors_absolut_lb) / (self.cluster_degree + 1)
            x_coor_lb_for_cluster = self.x_coors_absolut_lb + random.randint(0, self.cluster_degree) * x_coor_width_for_cluster_degree
            x_coor_ub_for_cluster = x_coor_lb_for_cluster + x_coor_width_for_cluster_degree
            dict_i_to_x_coor[i] = random.uniform(x_coor_lb_for_cluster + x_coor_width_for_cluster_degree * 0.2,
                                                 x_coor_ub_for_cluster - x_coor_width_for_cluster_degree * 0.2)

            y_coor_width_for_cluster_degree = (self.y_coors_absolut_ub -  self.y_coors_absolut_lb) / (self.cluster_degree + 1)
            y_coor_lb_for_cluster = self.y_coors_absolut_lb + random.randint(0, self.cluster_degree) * y_coor_width_for_cluster_degree
            y_coor_ub_for_cluster = y_coor_lb_for_cluster + y_coor_width_for_cluster_degree
            dict_i_to_y_coor[i] = random.uniform(y_coor_lb_for_cluster + y_coor_width_for_cluster_degree * 0.2,
                                                 y_coor_ub_for_cluster - y_coor_width_for_cluster_degree * 0.2)
        return dict_i_to_x_coor, dict_i_to_y_coor


class Scenario():

    def __init__(self, number_vehicles, relevant_customers): # todo remove T
        self.num_vecs = number_vehicles
        self.C = relevant_customers #[c for c in GIS_inputs.get_customers() if GIS_inputs.get_od_to_dist()[100, c] > lower_bound and GIS_inputs.get_od_to_dist()[100, c] < upper_bound]
        self.N = [index_hub] + self.C
        self.K = [k for k in range(self.num_vecs)]
        self.A = [(i,j) for i in self.N for j in self.N if i != j]


# #
# Class is intended to return the next scenario which can then be inserted into sub_opt_scenario
# When called scenario_creator.next(), the next scenario should be returned, inluding scen, cfg_params and io_excel

class Scenario_Creator():

    def _create_pandas_summary_skeleton(self):
        self.pd_cols = ['InstanceNo', 'Cluster_Deg', 'Quantity_Structure', 'DemandHeight', 'DemandAv', 'DemandStdDev', 'Num_Cust', 'Amount_Services', 'Capa_Size_Opt', 'Vehicle_UB','Max_Stops', 'Duration','Gap','ObjVal']
        pd_index = pandas.Index([i for i in range(len(self.scenarios))], name='Scenario_ID')
        pd_df_summary = pandas.DataFrame(np.zeros(( len(self.scenarios),len(self.pd_cols))), index=pd_index, columns=self.pd_cols)
        return pd_df_summary

    def __init__(self, root_directory, folder_title):
        self.folder_title = folder_title
        self.scenario_count = -1
        self.root_directory = root_directory

        # #
        # DEFINE the parameters to be studied HERE!;

        demand_cluster_options = [0] # options: [0,1,2]
        demand_quantities_options = ['HOMOGEN', 'HETEROGENEOUS'] # options: ['HOMOGEN', 'HETEROGENEOUS']
        demand_height_options = ['HIGH'] # options: ['HIGH', 'LOW']
        number_customers = [10]
        amount_services = [2, 3]
        capacity_size_options = ['L'] # options: ['S','L']
        vehicle_num_ubs = [20]
        max_stops = [3]
        instances_per_scen = [i for i in range (20)]
        self.fixed_seed = False

        self.scenarios = list(itertools.product(demand_cluster_options, demand_quantities_options, demand_height_options,
                                                     number_customers, amount_services, capacity_size_options,
                                                     vehicle_num_ubs, max_stops, instances_per_scen))

        self.scenarios_iter = iter(self.scenarios)
        # #
        # Parameters which we don't variate but are fed into the model
        self.T = [i for i in range(5)]


    def execute_all_scenarios(self):
        pd_df_summary = self._create_pandas_summary_skeleton()

        next_scenario = self.get_next_scenario()

        while next_scenario:
            (scen_count, next_scen_wrapped, sp_dem_strc), scenario, cfg_params, io_excel = next_scenario

            objVal, runtime, gap = sub_optimize_scenario(scenario, cfg_params, io_excel)

            # #
            # save details about current scenario
            dem_clus_opt, dem_q_opt, dem_h_opt, n_cust, n_serv, cap_size_opt, vehicle_ub, m_stops, instance_no_per_scen = next_scen_wrapped
            pd_df_summary.loc[[scen_count], self.pd_cols] = [instance_no_per_scen, dem_clus_opt, dem_q_opt, dem_h_opt,
                                                             sp_dem_strc.mean,
                                                             sp_dem_strc.std, n_cust, n_serv, cap_size_opt,
                                                             vehicle_ub, m_stops, runtime, gap, objVal]

            # #
            # go to next scenario
            next_scenario = self.get_next_scenario()

        pandas.set_option("display.max_rows", None, "display.max_columns", None)
        path_to_case_study_output_excel = self.root_directory +'/scenario_'+ self.folder_title + '/' + '_Summary_' + '.xlsx'
        writer = pandas.ExcelWriter(path_to_case_study_output_excel, engine='xlsxwriter')
        pd_df_summary.to_excel(writer, engine='xlsxwriter')
        writer.save()



    def save_sampled_locs_and_w(self, W_i, x_coors, y_coors, next_scen_wrapped):

        # #
        # Prep: unpack next_scenario; hence write necessary info in file name
        dem_clus_opt, dem_q_opt, dem_h_opt, n_cust, n_serv, cap_size_opt, vehicle_ub, m_stops, instance_no_per_scen = next_scen_wrapped

        string_scenario_info = 'dem_q_opt'+str(dem_q_opt)+'dem_h_opt'+str(dem_h_opt)+'n_cust'+str(n_cust)+'n_serv'+str(n_serv)
        path_to_case_study_output_excel = self.root_directory + '/scenario_' + self.folder_title + '/' + '_SpacStruc_'+string_scenario_info+'.xlsx'
        writer = pandas.ExcelWriter(path_to_case_study_output_excel, engine='xlsxwriter')

        # #
        # Save W
        pd_df_wi = pandas.DataFrame.from_dict(W_i, orient='index')
        print(pd_df_wi)
        pd_df_wi.to_excel(writer, engine='xlsxwriter',sheet_name='W_i')

        # #
        # X Coors
        pd_df_x_coors = pandas.DataFrame.from_dict(x_coors, orient='index')
        pd_df_x_coors.to_excel(writer, engine='xlsxwriter',sheet_name='XCoors')

        # #
        # y Coors
        pd_df_y_coors = pandas.DataFrame.from_dict(y_coors, orient='index')
        pd_df_y_coors.to_excel(writer, engine='xlsxwriter', sheet_name='YCoors')
        writer.save()

    # #
    # Aux Method which retrieves the next scenario from class object "self.scenarios" and
    # Generates all required parameters for that scenario to prepare it for a model run

    def get_next_scenario(self):
        next_scen_wrapped = next(self.scenarios_iter, None)
        if not next_scen_wrapped: return None
        else:
            dem_clus_opt, dem_q_opt, dem_h_opt, n_cust, n_serv, cap_size_opt, vehicle_ub, m_stops , instance_no_per_scen = next_scen_wrapped
            print("next scenario", self.scenario_count, " instance for that scenario :", instance_no_per_scen)

            # #
            # Create spatial demand structure for current instance
            sp_dem_strc = SpacialStructure(n_cust, n_serv, dem_clus_opt, dem_q_opt, dem_h_opt, 0, with_fixed_seed=self.fixed_seed)

            # #
            # we need scenario object
            scenario = Scenario(vehicle_ub, [i for i in range(n_cust)])

            # #
            # create cfg object
            services = [i for i in range(n_serv)]
            service_times = [0.1 for i in services]

            vehic_settings = VehicleSettings(n_serv,  cap_size_opt)

            cfg_params = fpvrps.FPVRPVecIndConfg(self.T,  W_i=sp_dem_strc.dict_i_s_to_total_demand,
                                                 w_i=sp_dem_strc.dict_i_s_to_daily_demand
                                                 , c=sp_dem_strc.dict_distance,
                                                 coordinates=(sp_dem_strc.coordinates_dict_x,
                                                              sp_dem_strc.coordinates_dict_y),
                                                 S=[i for i in range(n_serv)],
                                                 H=vehic_settings.H,
                                                 travel_time=sp_dem_strc.dict_duration, Q_h_s=vehic_settings.Q_h_s,
                                                 fixed_costs_h=vehic_settings.fixed_vehicle_costs,
                                                 service_time=service_times,  time_limit=8, stop_limit=m_stops, range_limit=200, cost_factor_per_km=1)

            # Create Excel Handler for current scenario
            io_excel = IOExcel(scenario, root_directory=self.root_directory,
                               scenario_id=self.folder_title, add_to_folder_title='',
                               title_excel_to_create_or_read="Com_Ex"+str(self.scenario_count)+"_DecisionvariableValues.xlsx",
                               titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
                                                        ['Customer', 'Vehicle', 'Day', 'ServiceType'],
                                                        ['ConfigType', 'Vehicle']),
                               output_tab_names=('Z', 'Y', 'Q', 'U'))

            # Safe demand data
            self.save_sampled_locs_and_w(W_i=sp_dem_strc.dict_i_s_to_total_demand,
                                         x_coors=sp_dem_strc.coordinates_dict_x,
                                         y_coors=sp_dem_strc.coordinates_dict_y, next_scen_wrapped=next_scen_wrapped)
            self.scenario_count += 1

            instance_info = self.scenario_count, next_scen_wrapped, sp_dem_strc
            return instance_info, scenario, cfg_params, io_excel


Scenario_Creator(_get_root_directory()+'/Program', '05_24_ExpI').execute_all_scenarios()

