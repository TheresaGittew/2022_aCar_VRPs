import pandas
import os
import numpy as np
import itertools
class ReaderCapaOptions:

    def _get_root_directory(self):
        root_directory_program = os.path.dirname(
            os.path.abspath("README.md"))  # for example: /Users/theresawettig/PycharmProjects/2022_aCar_VRPs/Program
        self.root_directory_project = os.path.dirname(root_directory_program)

    def __init__(self, services, path_to_capas='/GIS_Data/CaseStudy_CapacityOpt.csv'):
        self.path_to_capas = path_to_capas
        self._get_root_directory()
        self.services = services

        df = self._read_csv()
        df_prepared = self._prep_configs(df)
        self.df_ready = self._create_dict(df_prepared)

    def get_df(self):
        return self.df_ready

    def _read_csv(self):
        res = pandas.read_csv(self.root_directory_project + self.path_to_capas, delimiter=';')
        #print(res)
        return res

    # output should be: xyz
    def _prep_configs(self, df):
        df['ELEC'] = df['ELEC'].apply(lambda x: round(float((x).replace(',','.')), 2))
        df = df.set_index('Unnamed: 0')
        return df

    def _get_all_combis(self, current_service_list):
        indices = []
        for L in range(1, len(current_service_list) + 1):
            for subset in itertools.combinations(current_service_list, L):
                for elem in itertools.permutations(subset):
                    new_elem =  ', '.join(elem)
                    indices.append(new_elem)
        return indices

    def _create_dict(self, df):
        service_set_to_configs = {}
        key_error = False
        for s in self.services:
            combis_for_serviceset = self._get_all_combis(s)
            relevant_configs = {}
            config_count = 0
            for r in combis_for_serviceset:
                # print("next r: " , r)
                try: relevant_config = df.loc[r]
                except KeyError: key_error = True
                if not key_error:
                    # print("are in not key error part with " , r)
                    if isinstance(relevant_config, pandas.Series):
                        relevant_configs[config_count] = relevant_config.to_dict() # nested dict; first key: config_number; second key: service
                        config_count += 1
                    else:
                        for row_index in range(len(relevant_config.index)):
                            next_dataseries = relevant_config.iloc[row_index].to_dict()
                            relevant_configs[config_count] = next_dataseries
                            config_count +=1
                key_error = False

        return relevant_configs

        # wir brauchen eine funktion, die für jeder möglichen service-kombi die entsprechenden konfigurationen zuordnet




service_combis = [['WDS'], ['PNC'], ['ELEC'], ['ED'], ['WDS','PNC'],
                  ['WDS', 'ELEC'], ['WDS','ED'], ['PNC','ELEC'],
                  ['PNC','ED'],['ELEC','ED'], ['WDS','PNC','ELEC'],
                  ['WDS','PNC','ED'], ['WDS','ELEC','ED'],['PNC','ELEC','ED'],
                  ['WDS','PNC','ELEC','ED']]





class DummyForExcelInterface:

    def __init__(self, services):
        self.num_days = 5
        self.T = [i for i in range(self.num_days)]
        self.S = services


        reader = ReaderCapaOptions([self.S])

        self.Q_h_s = reader.get_df()
        self.H = list(self.Q_h_s.keys())

        self.fixed_costs = dict((h, 10000 + 2000 * len([i for i in self.Q_h_s[h].values() if i != 0.0])) for h in self.H)
        self.service_times = {'WDS': 0.0001, 'PNC': 0.1666, 'ELEC': 0.001, 'ED': 0.01}

        self.daily_demand_factors = {'WDS': 1, 'ELEC': 1, 'ED': 1, 'PNC': 1},

        # #
        # Inputs for consumption function
        daily_water_consumption_p_P = 3.2
        handy_battery_duration_in_days = 2
        elec_people_per_pack = 200

        ed_services_per_week = 0.25
        pnc_births_per_women = 4.04 # https://data.worldbank.org/indicator/SP.DYN.TFRT.IN?locations=ET
        pnc_fertility_span = 30 # number of years a pregant women could get a child
        required_visits_per_week = 3/52 # 3 services per pregnancy. As we only look at 1 week: /52


        # #
        # These functions are used to map the number of potential customers to the weekly demand values
        self.functions_to_consumption_per_T = {'WDS': (lambda x: x * daily_water_consumption_p_P * self.num_days),
                                               'ELEC': (lambda x: (x * self.num_days / handy_battery_duration_in_days)
                                                                  / elec_people_per_pack),
                                          'ED': (lambda x: x * ed_services_per_week),
                                               'PNC': (lambda y:  required_visits_per_week *
                                                                  (y * pnc_births_per_women)/ pnc_fertility_span)}
        #self.max_num_vehicles = 25
        self.time_limit = 8
        self.stop_limit = 3
        self.range_limit = 300


    def get_vehiclecapa_numdays_S(self):
        return self
#
# class DummyForExcelInterface_IC:
#
#     def __init__(self):
#         self.num_days = 5
#         self.T = [i for i in range(self.num_days)]
#         self.S = ['ELEC', 'PNC']
#         self.H = [0, 1]
#         self.Q_h_s = { (0, 'ELEC'): 1800, (0, 'PNC'): 25,
#                        (1, 'ELEC'): 1000, (1, 'PNC'): 25}
#
#         self.fixed_costs = {0: 60000, 1: 50000}
#
#         self.service_times = {'PNC': 0.166, 'ELEC': 0.00833333, 'ED':0.0833}
#
#         self.daily_demand_factors = {'ELEC': 1, 'ED': 1, 'PNC': 1},
#         self.functions_to_consumption_per_T = {'WDS': (lambda x: x * 3), 'ELEC': (lambda x: x * 1),
#                                                'ED': (lambda x: x * 1), 'PNC': (lambda y: y * 3 / 52)}
#
#
#     def get_vehiclecapa_numdays_S(self):
#         return self