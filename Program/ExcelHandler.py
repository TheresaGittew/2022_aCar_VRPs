import os

import gurobipy

import pandas as pd
import math

def get_path_str_for_scenario(scenario, root_directory):
    return root_directory  + '/Scenario_NumVec' + str(scenario.num_vecs) + '-LBs' \
                  + str(scenario.lower_bound) + '-UBs' + str(scenario.upper_bound)+'/'


class IOExcel:

    def __init__(self, scenario, root_directory, add_to_folder_title='', title_excel_to_create_or_read ="DecisionvariableValues.xlsx",
                 titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'], ['O', 'D', 'Vehicle', 'Day'],
                                          ['Customer', 'Vehicle', 'Day', 'ServiceType']), output_tab_names=('Z', 'Y', 'Q')):
        self.root_directory = root_directory
        self.scenario = scenario

        # #
        # create new folder path name for current scenario
        self.path_to_scenario_folder_str = root_directory + '/Scenario_NumVec' \
                                           + str(scenario.num_vecs) + '-LBs' + str(scenario.lower_bound) + '-UBs' + str(scenario.upper_bound) +'' + add_to_folder_title +'/'

        # #
        # create new folder for current scenario
        plot_dir = os.path.dirname(__file__)
        results_dir = os.path.join(plot_dir, self.path_to_scenario_folder_str)
        if not os.path.isdir(results_dir):
           os.makedirs(results_dir)

        # #
        #  save all relevant info about the (maybe yet to created) excel output file
        self.title_excel_to_create_or_read = title_excel_to_create_or_read
        self.titles_keys_per_dec_var = titles_keys_per_dec_var
        self.output_tab_names = output_tab_names

    def get_directory_name_for_scenario(self):
        return self.path_to_scenario_folder_str

    def _aux_create_df(self, dictionary, title_of_indices):
        df = pd.DataFrame.from_dict(dictionary, orient='index')
        df.reset_index(level=0, inplace=True)
        df[title_of_indices] = pd.DataFrame(df['index'].tolist(), index=df.index)
        df.drop(columns=['index'], inplace=True)
        df.rename(columns={0: 'Value'}, inplace=True)
        if isinstance(df['Value'][0], gurobipy.Var): df['Value'] = df['Value'].map(lambda x: x.X)
        df = df[df['Value'] > 0.001]
        return df

    def save_gurobi_res_in_excel(self, list_result_vars, model_objVal):

        # #
        # Step 1: Transform all variable dictionaries into  panda dataframes
        iterator_list_of_resulting_vars = iter(list_result_vars)
        dfs_output_dec_vars = []

        for indx_next_var in range(len(list_result_vars)):
            next_dec_var = next(iterator_list_of_resulting_vars)
            dfs_output_dec_vars.append(self._aux_create_df(next_dec_var, self.titles_keys_per_dec_var[indx_next_var]))

        # #
        # Step 2: save results in Excel file
        self.save_df_res_in_excel(dfs_output_dec_vars, model_objVal)

    def save_df_res_in_excel(self, dfs_output_dec_vars, objVal):

        # #
        #   Write the panda dataframes into excel file
        self.path_to_excel_file = self.path_to_scenario_folder_str + self.title_excel_to_create_or_read
        writer = pd.ExcelWriter(self.path_to_excel_file, engine='xlsxwriter')
        for i in range(len(dfs_output_dec_vars)):
            dfs_output_dec_vars[i].to_excel(writer, self.output_tab_names[i])

        # #
        # Step 3: Write objective value to pd dataframe and save
        pd.DataFrame([objVal]).to_excel(writer, 'objVal')
        writer.save()

    # If we create new results, save them to excel and read the results in the same run, the
    # name of the excel file is automatically retrieved from the method above.
    # otherwise, we do not need to newly create an excel file; if we want to access an existing excel file
    # we have to hand over the name of that excel file again
    def get_path_to_excel_file(self):
        return self.path_to_scenario_folder_str + self.title_excel_to_create_or_read

    def get_obj_val_from_excel(self, tab_name='objVal'):
        #writer = pd.ExcelWriter(self.path_to_scenario_folder_str + self.title_excel_to_create_or_read, engine='xlsxwriter')
        return pd.read_excel(self.path_to_scenario_folder_str + self.title_excel_to_create_or_read, sheet_name=tab_name)[0].values[0]


    def get_results_from_excel_to_df(self, with_multiindex=True):
        it_dec_var_names = iter(self.output_tab_names)
        dict_decvar_str_to_df = {}

        # #
        # version 1: get the dfs where each "key" is a normal column
        for i in range(len(self.output_tab_names)):
            next_var_str = it_dec_var_names.__next__()
            next_df = pd.read_excel(self.path_to_scenario_folder_str + self.title_excel_to_create_or_read, sheet_name=next_var_str)   # in case method is called without having safed gurobi results before, this option is relevant to hand over the link to the excel file

            # #
            # Here, we extract the columns that are relevant. Note that we currently manually add the value column
            # as "self.titles_keys_per_dict" only contains the non-value columns
            next_df = next_df[['Value'] + self.titles_keys_per_dec_var[i]]
            dict_decvar_str_to_df[self.output_tab_names[i]] = next_df


        # #
        # version 2: case it is needed where "keys" (eg customer, value, day...) are transformed to multi-index
        if with_multiindex:
            for i in range(len(self.output_tab_names)):
                next_df = dict_decvar_str_to_df[self.output_tab_names[i]]
                next_df = next_df.set_index(self.titles_keys_per_dec_var[i])
                print(next_df)
                dict_decvar_str_to_df[self.output_tab_names[i]] = next_df


        return dict_decvar_str_to_df




#io_excel = IOExcel()
