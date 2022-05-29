import pandas
import os
import numpy as np
import itertools

# #
# Proxy for prospective excel file in which the operator can enter relevant key facts about the fleet
# Please enter it directly inside the __init__() function.

class DummyForExcelInterface:

    def __init__(self, services):

        # #
        # *** ENTER INFO HERE ***
        self.num_days = 5
        self.T = [i for i in range(self.num_days)]  # number of days in time horizon
        self.S = services

        # value between 0 and 1 for each service corresponding; corresponding to the share of w_i from W_i
        self.daily_demand_factors = {'WDS': 1, 'ELEC': 1, 'ED': 1, 'PNC': 1}

        # #
        # Inputs for consumption function
        daily_water_consumption_p_P = 3.2
        handy_battery_duration_in_days = 2
        ed_services_per_week = 0.25
        required_visits_per_week = 3 / 52  # 3 services per pregnancy. As we only look at 1 week: /52


        # #
        # These functions are used to map the number of potential customers to the weekly demand values
        self.functions_to_consumption_per_T = {'WDS': (lambda x: x * daily_water_consumption_p_P * self.num_days),
                                               'ELEC': (lambda x: (x * self.num_days / handy_battery_duration_in_days)
                                                                ),
                                          'ED': (lambda x: x * ed_services_per_week),
                                               'PNC': (lambda y:  required_visits_per_week * y )}

        # Additional constraint values
        self.time_limit = 8
        self.stop_limit = 4
        self.range_limit = 200

        # # Do nothing here.
        self.S = services
        reader = ReaderCapaOptions([self.S])

        self.Q_h_s = reader.get_df() # Vehicle capacities obtained automatically for a given set of services
        self.H = list(self.Q_h_s.keys()) # Configurations obtained automatically for a given set of services


    def get_vehiclecapa_numdays_S(self):
        return self


class ReaderCapaOptions:

    def _get_root_directory(self):
        root_directory_program = os.path.dirname(
            os.path.abspath("README.md"))  # for example: /Users/theresawettig/PycharmProjects/2022_aCar_VRPs/Program
        self.root_directory_project = os.path.dirname(root_directory_program)

    def __init__(self, services, path_to_capas='/GIS_Data/Capacity_Options.csv'):
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
#        df['ELEC'] = df['ELEC'].apply(lambda x: round(float((x).replace(',','.')), 2))
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


