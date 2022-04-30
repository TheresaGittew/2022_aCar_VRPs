import xlsxwriter
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
from input_interface import  DummyForExcelInterface
import itertools
from fpvrp_ParameterInputClasses import InputGISReader
import random

num_digits_round = 2

class Result_Summarizer():

    def __init__(self, folder_name='/Program/04_18_CaseStudy_CI_0_Test',
                 relative_path_to_demand = '/GIS_Data/IC_Location_Data.csv',
                 relative_path_to_coors = '/GIS_Data/IC_Coordinates.csv',
                 relative_path_to_od_matrix = '/GIS_Data/IC_ODs.csv', path_to_output = '/Program/CaseStudy_Output'):
        self.relative_path_to_demand = relative_path_to_demand
        self.relative_path_to_coors = relative_path_to_coors
        self.relative_path_to_od_matrix = relative_path_to_od_matrix
        self.path_to_output = path_to_output

        self.folder_name = folder_name
        self.root_directory = self.get_root_directory()
        self.directory_to_read = self.root_directory + self.folder_name
        print(self.directory_to_read)

        self.customer_scenarios, self.dict_customerscen_to_percentage = self._get_customer_scenarios(self.directory_to_read)
        self.service_combis = list(self._get_services(self.directory_to_read))
        print("service combis" , self.service_combis)
        print("customer scenarios" , self.customer_scenarios)

        self.kpis = ['%Cov.','T.C.', 'Fx.C.', 'Vr.C.', 'T.Km.', 'N.V.', 'N.VT.', 'V.Ut.',
                     'Comp.T.', 'Gap[%]']

        # self.extract_excel_inputs('PNC', 1, 0.05)
        self._setup_pandas_summary(self.customer_scenarios, self.service_combis, self.kpis)

    def _get_gis(self, single_service_combi):
        input_interface = DummyForExcelInterface(single_service_combi).get_vehiclecapa_numdays_S()

        input_gis = InputGISReader(input_interface.daily_demand_factors[0],
                                   input_interface.functions_to_consumption_per_T,
                                   relative_path_to_demand=self.relative_path_to_demand,
                                   relative_path_to_coors=self.relative_path_to_coors,
                                   relative_path_to_od_matrix=self.relative_path_to_od_matrix,
                                   services=single_service_combi)
        return input_gis

    def _get_interface(self, single_service_combi):
        print("current service combi ", single_service_combi)
        print(DummyForExcelInterface(single_service_combi).Q_h_s)
        return DummyForExcelInterface(single_service_combi)




    def _map_services_list(self, service_combis_in_list): # for example [['WDS','PNC'],['WDS']]
        return [', '.join(lis) for lis in service_combis_in_list]

    def _map_single_service_list(self, service_combis_in_list): # for example ['WDS','PNC']
        return ', '.join(service_combis_in_list)

    def _setup_pandas_summary(self, customer_scenarios, service_combis, kpis):
        service_combis_mapped = self._map_services_list(service_combis)
        self.pd_index = pd.MultiIndex.from_tuples(list(itertools.product(service_combis_mapped, kpis)),
                                                  names=["S.Cmb.", "KPI"])
        self.pd_df_summary = pd.DataFrame(np.zeros((len(self.pd_index.values), len(customer_scenarios))),
                                          index=self.pd_index, columns=customer_scenarios)
        print(self.pd_df_summary)
        ## Add total costs
        print("Customer scnearois ", customer_scenarios)
        for c in customer_scenarios:
            print("Next customer scenario : ", c)



            for s in service_combis:
                s_to_string = self._map_single_service_list(s)
                excel_path = self._get_correct_excel(c, s)
                if excel_path:
                    # #
                    # Add percentage of current customer scenario
                    self.pd_df_summary[c][s_to_string, '%Cov.'] = self.dict_customerscen_to_percentage[c]
                    print(self.pd_df_summary)



                    # #
                    # add objective value - total costs - and computation time
                    print("here !! excel path: ", excel_path, "service: ", s, " cleint: ", c)
                    obj_val, comp_time, gap = self._get_total_costs_and_comp_time(excel_path)
                    self.pd_df_summary[c][s_to_string, 'T.C.'] = obj_val
                    self.pd_df_summary[c][s_to_string, 'Comp.T.'] = comp_time
                    self.pd_df_summary[c][s_to_string, 'Gap[%]'] = gap

                    # #
                    # add variable costs
                    self.pd_df_summary[c][s_to_string, 'Vr.C.'] = self._get_variable_costs(excel_path, self._get_gis(s))
                    self.pd_df_summary[c][s_to_string, 'T.Km.'] = self._get_variable_costs(excel_path, self._get_gis(s))

                    # #
                    # get fixed costs
                    self.pd_df_summary[c][s_to_string, 'Fx.C.'] = self._get_fixed_costs(excel_path, self._get_interface(s))

                    # #
                    # vehicle number and amount of different types
                    num_vecs, num_vec_types =  self._get_vehicle_number_and_num_types(excel_path)
                    self.pd_df_summary[c][s_to_string, 'N.V.'] = num_vecs
                    self.pd_df_summary[c][s_to_string, 'N.VT.'] = num_vec_types

                    # #
                    # utilization
                    self.pd_df_summary[c][s_to_string, 'V.Ut.'] = self._get_utilization(excel_path, num_vecs )


        pd.set_option("display.max_rows", None, "display.max_columns", None)
        path_to_case_study_output_excel = self.root_directory + self.path_to_output + '/' + self.folder_name.split('/')[-1]+'.xlsx'
        # print(path_to_case_study_output_excel)
        writer = pd.ExcelWriter(path_to_case_study_output_excel, engine='xlsxwriter')
        self.pd_df_summary.to_excel(writer, engine='xlsxwriter')
        writer.save()









        # todo
        # erst nur 0 en einfügen; nächsten schritte: sukzessive immer für passenden index u. Column den richtigen wert einfügen, am
           #  besten über Aufruf der einzelnen Methoden





    # it has to be assumed that for all services, we have the same customers
    #
    def _get_customer_scenarios(self, directory_to_read): # here, one subfolder is for example 'scenario_['PNC'] 12'


        folders = [x[0] for x in os.walk(directory_to_read)][1:]
        print(folders)
        extracted_customers_and_percentages = sorted(list(set([(int(f.split(" ")[-2]), float(f.split(" ")[-1])) for f in folders])), key= lambda x: x[0]) # extracts "['PNC'] 7", "['PNC'] 8", "['PNC'] 6"

        extracted_customers = [i[0] for i in extracted_customers_and_percentages] # returns customer id only
        #print(extracted_customers_and_percentages)

        extracted_shares = dict((i[0], i[1]) for i in extracted_customers_and_percentages) # returns customer percentage
        return extracted_customers, extracted_shares

    # def _get_customer_scenarios(self, directory_to_read): # here, one subfolder is for example 'scenario_['PNC'] 12'
    #     folders = [x[0] for x in os.walk(directory_to_read)][1:]
    #     extracted_customers_and_percentages = sorted(list(set([(int(f.split(" ")[-1])) for f in folders]))) # extracts "['PNC'] 7", "['PNC'] 8", "['PNC'] 6"
    #     extracted_customers = [i  for i in extracted_customers_and_percentages] # returns customer id only
    #     extracted_shares = dict((i, (i + 1 )/ 45) for i in extracted_customers_and_percentages) # returns customer percentage
    #     return extracted_customers , extracted_shares

    def _get_services(self, directory_to_read, sub=False):
        folders = [x[0] for x in os.walk(directory_to_read)][1:] if not sub else [x[0] for x in os.walk(directory_to_read)]
        folders = [f.replace("[","*") for f in folders]
        folders = [f.replace("]", "*") for f in folders]
        extract_scenarios = set([(f.split('*')[-2]) for f in folders])
        extracted_scenarios = [list(map(lambda x: x.replace("'",''),d)) for d in [e.split(',') for e in extract_scenarios]]
        extracted_scenarios_without_empty_space = [[d.replace(" ","") for d in combi] for combi in extracted_scenarios]
        #print(extracted_scenarios_without_empty_space)

        return extracted_scenarios_without_empty_space if not sub else extracted_scenarios_without_empty_space[0]

    def get_root_directory(self):
        root_directory_program = os.path.dirname(
        os.path.abspath("README.md"))  # for example: /Users/theresawettig/PycharmProjects/2022_aCar_VRPs/Program
        root_directory = os.path.dirname(root_directory_program)
        return root_directory

    # customer comes as tuple (0, 0.234) remember
    def _get_correct_excel(self, customer, service):
        #print('customer: ', customer)
        ##print(service)
        folders = [x[0] for x in os.walk(self.directory_to_read)][1:]
        for f in folders:
            s = self._get_services(f, True)
            #print("service ", service)
            #print(s)
            if int(f.split(" ")[-2]) == customer and self._get_services(f, True) == service:
                return f+'/'+'DecisionvariableValues.xlsx'

    def _get_total_costs_and_comp_time(self, path_to_excel):

        #print("path to excel ", path_to_excel)
        df = pd.read_excel(path_to_excel, sheet_name='objVal')
        # print(df)
        obj_val = round(df[0][0], num_digits_round)
        comp_time = round(df[0][1], num_digits_round)
        gap = round(df[0][2], num_digits_round)
        return obj_val, comp_time, gap

    def _get_variable_costs(self, path_to_excel, input_gis):
        np_array = np.array(pd.read_excel(path_to_excel, sheet_name='Y')[['O','D']])
        total_dist = 0
        for o_d_pair in np_array:
            total_dist += input_gis.get_od_to_dist()[o_d_pair[0], o_d_pair[1]]
        # print(total_dist)
        return round(total_dist, num_digits_round)

    def _get_fixed_costs(self, path_to_excel, interface):
        pd_df = pd.read_excel(path_to_excel, sheet_name='U')['ConfigType']
        print("fixed costs" , interface.fixed_costs)
        fixed_costs = sum(interface.fixed_costs[i] for i in list(pd_df))
        return round(fixed_costs, num_digits_round)

    def _get_vehicle_number_and_num_types(self, path_to_excel):
        pd_df = pd.read_excel(path_to_excel, sheet_name='U')['ConfigType']
        return len(pd_df.values), len(set(list(pd_df)))

    def _get_utilization(self, path_to_excel, num_vehicles, num_days=5):
        pd_df = len(set([tuple(i) for i in  np.array(pd.read_excel(path_to_excel, sheet_name='Q')[['Vehicle','Day']])]))
        utilization = pd_df / (num_vehicles * num_days)
        return round(utilization, num_digits_round)


Result_Summarizer(folder_name='/Program/04_25_ET',
                  relative_path_to_demand='/GIS_Data/ET_Location_Data.csv',
                  relative_path_to_coors='/GIS_Data/ET_Coordinates.csv',
                  relative_path_to_od_matrix='/GIS_Data/ET_ODs.csv')

