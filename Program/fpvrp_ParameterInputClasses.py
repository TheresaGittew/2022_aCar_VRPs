import os
import pandas as pd
import random
index_hub = 100

class InputGISReader:

    def __init__(self, relative_path_to_demand='/GIS_Data/ET_Location_Data.csv',
                 relative_path_to_coors='/GIS_Data/ET_Coordinates.csv',
                 relative_path_to_od_matrix='/GIS_Data/ET_ODs.csv', services=('WDS','ELEC','ED','PNC'),
                 daily_demand_factors={'WDS':1,'ELEC':1,'ED':1,'PNC':1},
                 functions_to_consumption_per_T={'WDS': (lambda x: x * 0.25),'ELEC': (lambda x: x * 0.25),'ED': (lambda x: x * 0.25),'PNC': (lambda y: y * 3 / 52)}):

        self.rltv_path_to_demand = relative_path_to_demand
        self.rltv_path_to_coors = relative_path_to_coors
        self.rltv_path_to_od_matrx = relative_path_to_od_matrix
        self.services = services
        self.daily_demand_factors = daily_demand_factors
        self.functions_to_consumption_per_T = functions_to_consumption_per_T

        # extract results
        self._get_root_directory()

        self._read_coordinates()

        self._read_matrix()

        self._read_demand_data()
        self._map_demand_data()
        self._create_daily_demands()


    def get_customers(self):
        return self.customers

    # Get root directory
    def _get_root_directory(self):
        root_directory_program = os.path.dirname(os.path.abspath("README.md")) # for example: /Users/theresawettig/PycharmProjects/2022_aCar_VRPs/Program
        self.root_directory_project = os.path.dirname(root_directory_program)

    #
    # important: demand_type_names order has to match the order in the .csv file
    def _read_demand_data(self):

        path_to_real_demand = self.root_directory_project + self.rltv_path_to_demand

        pds_csv_wide = pd.read_csv(path_to_real_demand, delimiter=';')
        # Now we have this:
        #           ClusterId  Service_type    value
        # 0            2          WDS          2806,157477
        # 1            4          WDS          1501,658731

        pds_narrow = pds_csv_wide.melt(id_vars='ClusterId', var_name='Service_type')
        pds_cols_to_indices = pds_narrow.set_index(['ClusterId','Service_type'])

        # Now we have this:
        #                            value
        # ClusterId  Service_type
        # 2           WDS           2806,157477
        # 4           WDS           1501,023
        # 7           WDS          ...

        pds_cols_to_indices_without_hub = pds_cols_to_indices.drop(index=100, level=0)  # remove hub

        # adjust format of demand value (from string to float)
        pds_cols_to_indices_without_hub['value'] = pds_cols_to_indices_without_hub['value'].apply(lambda x: float((x).replace(',','.')))

        # generates one dictionary basically for each column; we only have column with title 'value'
        # get the 'inner dict' for column 'value'
        dict_all_columns = pds_cols_to_indices_without_hub.to_dict()
        self.dict_i_s_to_total_demand = dict_all_columns['value']

    def _map_demand_data(self):
        self.dict_i_s_to_total_demand = dict(((cust, service), self.functions_to_consumption_per_T[service](v))
                                             for (cust, service), v in self.dict_i_s_to_total_demand.items())

    def get_total_demands(self):
        return self.dict_i_s_to_total_demand


    def _create_daily_demands(self):
        self.dict_i_s_to_daily_demand = dict(((cust, service), v * self.daily_demand_factors[service])
                                             for (cust, service), v in self.dict_i_s_to_total_demand.items())

    def get_daily_demands(self):
        return self.dict_i_s_to_daily_demand

    def _read_coordinates(self):
        pd_coors = pd.read_csv(self.root_directory_project + self.rltv_path_to_coors, delimiter=';')
        pd_coors_with_index = pd_coors.set_index('ClusterId')
        pd_coors_with_index['Latitude'] = pd_coors_with_index['Latitude'].apply(lambda x: float((x).replace(',','.')))
        pd_coors_with_index['Longitude'] = pd_coors_with_index['Longitude'].apply(lambda x: float((x).replace(',', '.')))
        coors_dict = pd_coors_with_index.to_dict()
        self.coordinates_dict_x = coors_dict['Latitude']
        self.coordinates_dict_y = coors_dict['Longitude']
        self.customers = [i for i in list(pd_coors['ClusterId']) if i != 100]
        return

    def get_coors(self):
        return self.coordinates_dict_x, self.coordinates_dict_y

    def _read_matrix(self):
        self.path_to_OD_matrix = self.root_directory_project + self.rltv_path_to_od_matrx
        pd_ods = pd.read_csv(self.root_directory_project + self.rltv_path_to_od_matrx, delimiter=';')

        # 1: Remove all links that connect a node to itself (otherwise the model picks these connections only)
        relevant_indices = pd_ods.index[(pd_ods['FROM_ID'] == pd_ods['TO_ID'])]
        pd_ods = pd_ods.drop(index=relevant_indices)



        # 2. Transform dataframe so we can easily convert it to a dictionary
        pd_ods_with_ind = pd_ods.set_index(['FROM_ID','TO_ID'])
        pd_ods_with_ind['DURATION_H'] = pd_ods_with_ind['DURATION_H'].apply(lambda x: float((x).replace(',', '.')))
        pd_ods_with_ind['DIST_KM'] = pd_ods_with_ind['DIST_KM'].apply(lambda x: float((x).replace(',', '.')))
        dict = pd_ods_with_ind.to_dict()
        self.dict_duration = dict['DURATION_H']
        self.dict_distance = dict['DIST_KM']

    def get_od_to_time(self):
        return self.dict_duration

    def get_od_to_dist(self):
        return self.dict_distance




class DummyForExcelInterface:

    def __init__(self):
        self.num_days = 5
        self.T = [i for i in range(self.num_days)]
        self.S = ['WDS','PNC']  # important: stick to order in csv file!
        # self.S = ['WDS']
        capacities = {'WDS': 1000}
        #self.vehicle_capa = dict(((i, c), capacities[c]) for i in range(15) for c in list(capacities.keys()))

    #
    def get_vehiclecapa_numdays_S(self):
        return 0, self.T, self.S


class Scenario():

    # def find_relevant_customers(arcs_list, customer_num, min_distance_bekoji, max_distance_bekoji):
    #     lis = [c for c in range(1, customer_num) if
    #            arcs_list[0, c][1] > min_distance_bekoji and arcs_list[0, c][1] < max_distance_bekoji]
    #     return lis

    def __init__(self, number_vehicles, lower_bound, upper_bound, GIS_inputs, size=10): # todo remove T

        self.num_vecs = number_vehicles
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

        self.C = [c for c in GIS_inputs.get_customers() if GIS_inputs.get_od_to_dist()[100, c] > lower_bound and GIS_inputs.get_od_to_dist()[100, c] < upper_bound]
        random.seed(10)
        self.C = random.choices(self.C, k=15)
        print(self.C)

        print("Relevant customers" , self.C)
        self.N = [index_hub] + self.C
        self.K = [k for k in range(self.num_vecs)]
        self.A = [(i,j) for (i,j) in GIS_inputs.get_od_to_dist().keys() if i in self.N and j in self.N ]


