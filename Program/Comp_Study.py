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
# What we have to define:
# Number of configuration options

# Get root directory
def _get_root_directory():
    root_directory_program = os.path.dirname(
        os.path.abspath("README.md"))  # for example: /Users/theresawettig/PycharmProjects/2022_aCar_VRPs/Program
    return os.path.dirname(root_directory_program)

class VehicleSettings():

    def __init__(self, num_services, capa_size_opt):

        self.capa_size = capa_size_opt
        #self.capa_struct = capa_structure_options[capa_structure_opt_choice]
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
        # print("services per combi : ", all_combis)
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
        print(self.Q_h_s)
        self.fixed_vehicle_costs = self._generate_vehicle_costs()
        print(self.fixed_vehicle_costs)

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



#vs = VehicleSettings(4, 0)
#print(vs.get_Q_h_s())


class SpacialStructure():

    def __init__(self, num_customers, num_services, cluster_degree_choice=0, demand_q_opt='HOMOGEN', demand_height='HIGH', w_i_choice=0, cluster_degree=(0,1,2),
                 w_i_options=('EQ_W', 'HALF_W')):
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
        random.seed(42)
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
        print ("euclidean distance : ", round(np.sqrt([x_distance ** 2 + y_distance ** 2])[0],2) * 40)
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

    # def find_relevant_customers(arcs_list, customer_num, min_distance_bekoji, max_distance_bekoji):
    #     lis = [c for c in range(1, customer_num) if
    #            arcs_list[0, c][1] > min_distance_bekoji and arcs_list[0, c][1] < max_distance_bekoji]
    #     return lis

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
        print(path_to_case_study_output_excel)
        writer = pandas.ExcelWriter(path_to_case_study_output_excel, engine='xlsxwriter')
        pd_df_summary.to_excel(writer, engine='xlsxwriter')
        writer.save()
        #/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/scenario_05_28_CompExTest_STANDARD_10_Cust_3_Services




    def __init__(self, root_directory, folder_title):
        self.folder_title = folder_title
        self.scenario_count = -1
        self.root_directory = root_directory+'/Program/05_09_CompEx'
        print(self.root_directory)

        # #
        # Parameters to variate in study
        demand_cluster_options = [0]
        demand_quantities_options = ['HOMOGEN']
        demand_height_options = ['HIGH', 'LOW']
        number_customers = [12]
        amount_services = [2]
        capacity_size_options = ['L']
        vehicle_num_ubs = [20]
        max_stops = [3]



        # #
        # Parameters to variate in study
        demand_cluster_options = [0]
        demand_quantities_options = ['HOMOGEN']
        demand_height_options = ['HIGH']
        number_customers = [10]
        amount_services = [3]
        capacity_size_options = ['L']
        vehicle_num_ubs = [20] #zuvor: 15
        max_stops = [3]
        instances_per_scen = [i for i in range(20)]

        self.scenarios = list(itertools.product(demand_cluster_options, demand_quantities_options, demand_height_options,
                                                     number_customers, amount_services, capacity_size_options,
                                                     vehicle_num_ubs, max_stops, instances_per_scen))
        print(self.scenarios)

        self.scenarios_iter = iter(self.scenarios)

        # #
        # Parameters which we don't variate but are fed into the model
        self.T = [i for i in range(5)]

    def get_next_scenario(self):
        next_scen_wrapped = next(self.scenarios_iter, None)
        if not next_scen_wrapped: return None
        else:
            dem_clus_opt, dem_q_opt, dem_h_opt, n_cust, n_serv, cap_size_opt, vehicle_ub, m_stops , instance_no_per_scen = next_scen_wrapped
            print("next scenario", self.scenario_count, " instance for that scenario :", instance_no_per_scen)

            # #
            # Create spatial demand structure for current instance
            sp_dem_strc = SpacialStructure(n_cust, n_serv, dem_clus_opt, dem_q_opt, dem_h_opt, 0)

            # #
            # we need scenario object
            scenario = Scenario(vehicle_ub, [i for i in range(n_cust)])

            # #
            # create cfg object
            services = [i for i in range(n_serv)]
            service_times = [0.2 for i in services]

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

            # Anlegen Excel-Objekt als Handler der Ergebnisse (ohne Nachbearbeitung)
            io_excel = IOExcel(scenario, root_directory=self.root_directory,
                               scenario_id=self.folder_title, add_to_folder_title='',
                               title_excel_to_create_or_read="Com_Ex"+str(self.scenario_count)+"_DecisionvariableValues.xlsx",
                               titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
                                                        ['Customer', 'Vehicle', 'Day', 'ServiceType'],
                                                        ['ConfigType', 'Vehicle']),
                               output_tab_names=('Z', 'Y', 'Q', 'U'))
            self.scenario_count += 1

            instance_info = self.scenario_count, next_scen_wrapped, sp_dem_strc

            return instance_info, scenario, cfg_params, io_excel

#s = Scenario_Creator(_get_root_directory())
#sub_optimize_scenario(scenario, cfg_params, io_excel)
Scenario_Creator(_get_root_directory(), '05_28_CB_10_Cust_3_Services').execute_all_scenarios()



def read_comp_studies_excel():
    pass