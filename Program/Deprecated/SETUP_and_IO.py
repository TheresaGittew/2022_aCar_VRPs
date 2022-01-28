import os

import gurobipy

import pandas as pd
import math



def get_path_for_scenario_results_file(scenario, name_file='DecisionvariableValues.xlsx', root_directory='Results'):
    return root_directory + '/Scenario_NumVec' + str(scenario.num_vecs) + '-LBs' \
    + str(scenario.lower_bound) + '-UBs' + str(scenario.upper_bound) + '/'+name_file


def get_path_for_scenario_preprocessing_file(scenario, name_file='Preprocessing_Inputs.xlsx', root_directory='Results'):
    return root_directory +'/Scenario_NumVec' + str(scenario.num_vecs) + '-LBs' \
           + str(scenario.lower_bound) + '-UBs' + str(scenario.upper_bound) + '/'+name_file


# creates a new folder for current run
# def create_directory_for_scenario(scenario, root_directory='Results'):
#     plot_dir = os.path.dirname(__file__)
#     results_dir = os.path.join(plot_dir, get_path_str_for_scenario(scenario, root_directory))
#
#     if not os.path.isdir(results_dir):
#         os.makedirs(results_dir)
#     return results_dir

# uses existing folder for current scenario to save used input data
def save_preprocessing_results_in_csv(R, P,  C_p, C_ps, demand, scenario, root_directory='Results'):
    # convert to pandas dataframes
    df_R = pd.DataFrame.from_dict(R, orient='index')
    df_P = pd.DataFrame.from_dict(P, orient='index')
    df_Cp = pd.DataFrame.from_dict(C_p, orient='index')
    df_dem = pd.DataFrame.from_dict(demand, orient='index')
    df_Cps = pd.DataFrame.from_dict(C_ps, orient='index')


    # Routes
    df_R = df_R.rename(columns=lambda s: 'Stop '+ str(s))
    df_R.reset_index(level=0, inplace=True)
    df_R.rename(columns={'index': 'RouteId'}, inplace=True)

    # Schedules
    df_P = df_P.rename(columns=lambda s: 'Day Visit No.' + str(s))
    df_P.reset_index(level=0, inplace=True)
    df_P.rename(columns={'index': 'ScheduleId'}, inplace=True)

    # Schedules for customers
    df_Cp = df_Cp.rename(columns=lambda s: 'Selected Schedule')
    df_Cp.reset_index(level=0, inplace=True)
    df_Cp.rename(columns={'index': 'Customer'}, inplace=True)

    # Schedules for customers and services
    df_Cps.reset_index(level=1, inplace=True)
    df_Cps.reset_index(level=0, inplace=True)
    df_Cps.rename(columns={'index': 'Customer', 'level_1':'Servicetype'}, inplace=True)

    # demands
    df_dem.reset_index(level=1, inplace=True)
    df_dem.reset_index(level=0, inplace=True)
    df_dem.rename(columns={'index':'CustomerId', 'level_1':'ScheduleId'}, inplace=True)


    # # create new excel writer, using the given directory and the file name specified below
    file_name = "Preprocessing_Inputs.xlsx"
    relative_path_to_excel = get_path_str_for_scenario(scenario, root_directory) + file_name
    writer = pd.ExcelWriter(relative_path_to_excel, engine='xlsxwriter')
    #
    # # create new excel file
    df_R.to_excel(writer, 'Routes')
    df_P.to_excel(writer, 'Schedules')
    df_Cp.to_excel(writer, 'CustomerSchedules')
    df_dem.to_excel(writer, 'DemandsForSchedules')
    df_Cps.to_excel(writer, 'CustomerServiceSchedules')
    #
    writer.save()

# returns computation-intensive temp. results from preprocessing (P, R, and C_p)
def get_preprocessing_results_from_csv(scenario, root_directory='Results'):

    def _convert_list(lis_values):
        return list(map(lambda z: int(z) , filter(lambda y: not math.isnan(y), (map(lambda x: float(x), list(lis_values))))))

    def _aux_create_dict_from_excel(tab_name, col_name_to_index, relative_excel_path):
        #
        pd_df = pd.read_excel(relative_excel_path, sheet_name=tab_name)
        pd_df.set_index([col_name_to_index], inplace=True)
        pd_df.drop(columns=['Unnamed: 0'], inplace=True)
        out_dict_temp = pd_df.to_dict(orient='index')
        return dict((k, _convert_list(v.values())) for k, v in out_dict_temp.items())


    tab_names_default = ['Routes', 'Schedules', 'CustomerSchedules']
    tab_names_special = ['DemandsForSchedules']
    col_names = ['RouteId', 'ScheduleId', 'Customer']

    file_name = "Preprocessing_Inputs.xlsx"
    relative_path_to_excel = get_path_str_for_scenario(scenario, root_directory) + file_name

    R = _aux_create_dict_from_excel(tab_names_default[0], col_names[0], relative_path_to_excel)
    P = _aux_create_dict_from_excel(tab_names_default[1], col_names[1], relative_path_to_excel)
    C_p = _aux_create_dict_from_excel(tab_names_default[2], col_names[2], relative_path_to_excel)

    return R, P, C_p


def save_gurobi_res_in_excel(PVRP_obj, scenario, root_directory='Results'):

    def _aux_create_df(dictionary, title_of_indices):
        df = pd.DataFrame.from_dict(dictionary, orient='index')
        df.reset_index(level=0, inplace=True)
        df[title_of_indices] = pd.DataFrame(df['index'].tolist(), index=df.index)
        df.drop(columns=['index'],inplace=True)
        df.rename(columns={0: 'Value'}, inplace=True)
        df['Value'] = df['Value'].map(lambda x: x.X)
        df = df[df['Value'] > 0.5]
        return df

    def _save_df_in_excel(df, excel_writer, tab_name):

        df.to_excel(excel_writer, tab_name)
        return

    x = PVRP_obj.x
    y = PVRP_obj.y
    #z = PVRP_obj.z
    output_tab_names = ['X','Y']
    output_dec_vars = [x, y]
    titles_of_keys_per_dec_var = [['RouteId', 'Day'], ['Customer','ScheduleId'], ['RouteId','Customer','Day']]

    dfs_output_dec_vars = []
    for v in range(len(output_dec_vars)):
        dfs_output_dec_vars.append(_aux_create_df(output_dec_vars[v], titles_of_keys_per_dec_var[v]))

    # # create new excel writer, using the given directory and the file name specified below
    file_name = "DecisionvariableValues.xlsx"
    relative_path_to_excel = get_path_str_for_scenario(scenario, root_directory) + file_name
    writer = pd.ExcelWriter(relative_path_to_excel, engine='xlsxwriter')

    for i in range(len(output_dec_vars)):
        _save_df_in_excel(dfs_output_dec_vars[i], writer, output_tab_names[i])

    writer.save()
    pass

# list of resulting vars includes all decision variables
# note that the order of the elements in list_of_resulting_vars has to match with the titles_keys_per_dec_var
# so we assume we start with z, y, and q. Same holds for output tab names
def save_gurobi_res_in_excel_fpvrp(list_result_vars, model_objVal,
                                   relative_path_to_excel,
                                   titles_keys_per_dec_var=(['Customer', 'Vehicle', 'Day'],
                                                            ['O', 'D', 'Vehicle', 'Day'], ['Customer', 'Vehicle', 'Day', 'ServiceType']),
                                    output_tab_names=('Z', 'Y', 'Q'), from_gurobi=True):
    # print("titels keys per dict ", titles_keys_per_dec_var)
    def _aux_create_df(dictionary, title_of_indices):
        #print("current dict: " , " title of ind", title_of_indices)
        df = pd.DataFrame.from_dict(dictionary, orient='index')
        df.reset_index(level=0, inplace=True)
        #print(df['index'])
        df[title_of_indices] = pd.DataFrame(df['index'].tolist(), index=df.index)
        df.drop(columns=['index'],inplace=True)
        df.rename(columns={0: 'Value'}, inplace=True)
        if isinstance(df['Value'][0], gurobipy.Var) : df['Value'] = df['Value'].map(lambda x: x.X)
        df = df[df['Value'] > 0.5]
        return df

    def _save_df_in_excel(df, excel_writer, tab_name):

        df.to_excel(excel_writer, tab_name)
        return

    iterator_list_of_resulting_vars = iter(list_result_vars)
    dfs_output_dec_vars = []

    for indx_next_var in range(len(list_result_vars)):
        next_dec_var = next(iterator_list_of_resulting_vars)
        dfs_output_dec_vars.append(_aux_create_df(next_dec_var, titles_keys_per_dec_var[indx_next_var]))

    writer = pd.ExcelWriter(relative_path_to_excel, engine='xlsxwriter')

    for i in range(len(list_result_vars)):
        _save_df_in_excel(dfs_output_dec_vars[i], writer, output_tab_names[i])

    pd.DataFrame([model_objVal]).to_excel(writer, 'objVal')
    writer.save()
    pass


def save_gurobi_res_in_excel_with_services(PVRP_obj, scenario, relative_path_to_excel):

    def _aux_create_df(dictionary, title_of_indices):

        df = pd.DataFrame.from_dict(dictionary, orient='index')
        df.reset_index(level=0, inplace=True)  # remove all indices; all "keys" of the given dict are columns then
        df[title_of_indices] = pd.DataFrame(df['index'].tolist(), index=df.index)  # we create a new dataframe from the tuples (keys), so that they go into separate columns, and "merge" it with the exisitng index
        df.drop(columns=['index'],inplace=True) # drop index column
        df.rename(columns={0: 'Value'}, inplace=True)
        df['Value'] = df['Value'].map(lambda x: x.X)
        df = df[df['Value'] > 0.5]
        return df

    def _save_df_in_excel(df, excel_writer, tab_name):

        df.to_excel(excel_writer, tab_name)
        return

    x = PVRP_obj.x
    y = PVRP_obj.y
    h = PVRP_obj.h
    #z = PVRP_obj.z
    output_tab_names = ['X','Y','H']
    output_dec_vars = [x, y, h]
    titles_of_keys_per_dec_var = [['RouteId', 'Day', 'Service'], ['Customer','ScheduleId', 'Service'], ['Vehicle','RouteId','Day']]

    dfs_output_dec_vars = []
    for v in range(len(output_dec_vars)):
        dfs_output_dec_vars.append(_aux_create_df(output_dec_vars[v], titles_of_keys_per_dec_var[v]))

    # # create new excel writer, using the given directory and the file name specified below

    writer = pd.ExcelWriter(relative_path_to_excel, engine='xlsxwriter')

    for i in range(len(output_dec_vars)):
        _save_df_in_excel(dfs_output_dec_vars[i], writer, output_tab_names[i])

    writer.save()
    pass



def get_x_df(path_results):
    writer = pd.ExcelWriter(path_results, engine='xlsxwriter')
    df = pd.read_excel(writer, sheet_name='X')
    return df[['Value', 'RouteId', 'Day']]

def get_x_df_service(path_results):
    writer = pd.ExcelWriter(path_results, engine='xlsxwriter')
    df = pd.read_excel(writer, sheet_name='X')
    return df[['Value', 'RouteId', 'Day', 'Service']]

def get_h_df(path_results):
    writer = pd.ExcelWriter(path_results, engine='xlsxwriter')
    df = pd.read_excel(writer, sheet_name='H')
    return df[['Value', 'Vehicle', 'RouteId', 'Day']]

# creates a dict where the key is the customer and the value is the selected schedule
def get_y(path_results):
    writer = pd.ExcelWriter(path_results, engine='xlsxwriter')

    df = pd.read_excel(writer, sheet_name='Y')
    dict_ys = df.to_dict(orient='index')
    return dict((v['Customer'], v['ScheduleId']) for k, v in dict_ys.items())

def get_y_dict_services(path_results):
    writer = pd.ExcelWriter(path_results, engine='xlsxwriter')

    df = pd.read_excel(writer, sheet_name='Y')
    dict_ys = df.to_dict(orient='index')
    return dict(((v['Customer'],v['Service']), v['ScheduleId']) for k, v in dict_ys.items())

def get_nodes_per_route(route_id, path_preprocessing):
    writer = pd.ExcelWriter(path_preprocessing, engine='xlsxwriter')
    df = pd.read_excel(writer, sheet_name='Routes')

    cols_to_show = [i for i in range(1, len(df.columns))]
    relevant_route = df.iloc[route_id, cols_to_show]
    nodes_in_route = list(map(lambda x: int(x), filter(lambda x: not math.isnan(x), list(relevant_route[1:]))))
    return nodes_in_route


def get_customer_schedules(customer, path_results):
    xlsx_writer = pd.ExcelWriter(path_results, engine='xlsxwriter')
    df = pd.read_excel(xlsx_writer, sheet_name='Y')
    schedule_this_customer = df.loc[customer]


# returns pd dataframe
# access data of a particular row with: df.loc[(1,2)], where 1 would be the customer id and 2 the schedule id
def get_demand_for_schedules(path_preprocessing):
    writer = pd.ExcelWriter(path_preprocessing, engine='xlsxwriter')
    df = pd.read_excel(writer, sheet_name='DemandsForSchedules')
    df = df.drop(columns=['Unnamed: 0'])
    df = df.set_index(keys=['CustomerId','ScheduleId'])
    return df


def get_days_in_schedule(scheduleid, path_preprocessing):
    writer = pd.ExcelWriter(path_preprocessing, engine='xlsxwriter')
    df = pd.read_excel(writer, sheet_name='Schedules')
    relevant_cols = [i for i in range(2, len(df.columns))]
    relevant_days = list((df.iloc[scheduleid, relevant_cols]).dropna())
    return relevant_days


# creates a dict and a pd dataframe where the key / index is the day and the value is the list of routes of that day
def create_table_day_to_routes(x_df):
    dict_day_to_routes = {}
    max_day = max(list(x_df['Day']))
    for d in range(max_day):
        vals = list((x_df.query('Day == ' + str(d))['RouteId']).values)
        dict_day_to_routes[d] = vals

    dict_converted_for_df = dict ((k, [v]) for k,v in dict_day_to_routes.items())
    df_day_to_routes = pd.DataFrame.from_dict(dict_converted_for_df, orient='index')
    df_day_to_routes = df_day_to_routes.rename(columns={0:'RouteIds'})
    return dict_day_to_routes, df_day_to_routes




def get_visited_customers_per_day_rtd_and_service(x_df, y_dict, h_df, S, path_preprocessing):
    h_dict_transformed = (h_df[['Vehicle','RouteId','Day']]).to_dict(orient='index')

    vehicle_routeid_day_services_to_visited_nodes = {}
    for i in h_dict_transformed.keys():
        current_route_id = h_dict_transformed[i]['RouteId']
        current_day_for_route = h_dict_transformed[i]['Day']
        current_vehicle = h_dict_transformed[i]['Vehicle']
        for s in S:
            if not x_df[(x_df['Day'] == current_day_for_route) & (x_df['RouteId'] == current_route_id ) & (x_df['Service'] == 'PNC')].empty:
               # print(x_df.query('Day =='+str(current_day_for_route)+' and Service == '+str(s)+' and RouteId == '+str(current_route_id)).values )
                nodes_on_route = get_nodes_per_route(current_route_id, path_preprocessing)

                # For The current route id and day, find all visited customers
                visited_customers_on_route = []
                for c in nodes_on_route:   # important for keeping correct order
                    if (c,s) in y_dict:
                        selected_schedl_id = y_dict[c, s]   # check the selected schedule for current customer
                        days = get_days_in_schedule(selected_schedl_id, path_preprocessing)
                        if current_day_for_route in days:
                            visited_customers_on_route.append(c)

                # #
                # if we checked all potential nodes, we move on with next route

                vehicle_routeid_day_services_to_visited_nodes[current_vehicle, current_day_for_route, current_route_id, s] = visited_customers_on_route
    return vehicle_routeid_day_services_to_visited_nodes


def get_visited_customers_per_day_and_rtd(x_df, y_dict, path_preprocessing):
    x_dict_transformed = (x_df[['RouteId','Day']]).to_dict(orient='index')

    visited_customer_per_day_and_rtd = {}
    for i in x_dict_transformed.keys():
        current_route_id = x_dict_transformed[i]['RouteId']
        current_day_for_route = x_dict_transformed[i]['Day']

        nodes_on_this_route = get_nodes_per_route(current_route_id, path_preprocessing)

        ##
        # For The current route id and day, find all visited customers
        visited_customers_on_route = []
        for c in nodes_on_this_route:   # important for keeping correct order
            if c in y_dict:
                selected_schedl_id = y_dict[c]   # check the selected schedule for current customer
                days = get_days_in_schedule(selected_schedl_id, path_preprocessing)
                if current_day_for_route in days:
                    visited_customers_on_route.append(c)

        # #
        # if we checked all potential nodes, we move on with next route
        visited_customer_per_day_and_rtd[current_day_for_route, current_route_id] = visited_customers_on_route
    return visited_customer_per_day_and_rtd


def _get_loads_for_day_and_route_id(day, route_id, visited_customer_per_day, y_dict, df_customer_schedid_to_demand):
    visited_custs_on_route = visited_customer_per_day[day, route_id]
    dict_visited_custs_to_route_demands = dict((i, df_customer_schedid_to_demand.loc[(i, y_dict[i])]['PNC']) for i in visited_custs_on_route)
    return dict_visited_custs_to_route_demands


def _get_loads_for_day_and_route_id_services(day, route_id, vehicle, service, visited_customer_per_day, y_dict, df_customer_schedid_to_demand):
    visited_custs_on_route = visited_customer_per_day[vehicle, day, route_id, service]
    dict_visited_custs_to_route_demands = dict((i, df_customer_schedid_to_demand.loc[(i, y_dict[i, service])][service]) for i in visited_custs_on_route)
    return dict_visited_custs_to_route_demands


def get_loads_for_day_and_route_meta(path_preprocessing, path_results):

    # setup
    x_dict = get_x_df(path_results)
    y_dict = get_y(path_results)

    dict_day_routeid_to_visited_custs = get_visited_customers_per_day_and_rtd(x_dict, y_dict, path_preprocessing)
    day_route_id_keys = list(dict_day_routeid_to_visited_custs.keys())

    customer_schedid_to_demand = get_demand_for_schedules(path_preprocessing)

    # loop through days and routes
    dict_day_routeid_to_loads = {}
    for day, route_id in day_route_id_keys:
        dict_visited_custs_to_demands = _get_loads_for_day_and_route_id(day, route_id, dict_day_routeid_to_visited_custs, y_dict, customer_schedid_to_demand)

        # we use dict_day_routeid_to_visited_custs to make sure we stick to the original order of visits
        visited_custs = dict_day_routeid_to_visited_custs[day, route_id]
        demands_visited_custs = [dict_visited_custs_to_demands[c] for c in visited_custs]
        loads_visited_custs = [(visited_custs[indx], sum(demands_visited_custs[indx:])) for indx in range(len(demands_visited_custs))]
        dict_day_routeid_to_loads[day, route_id] = loads_visited_custs

    return dict_day_routeid_to_loads


def get_loads_for_day_route_and_service_meta(path_preprocessing, path_results):

    # setup
    x_dict = get_x_df_service(path_results)
    y_dict = get_y_dict_services(path_results)
    h_df = get_h_df(path_results)
    dict_day_routeid_to_visited_custs = get_visited_customers_per_day_rtd_and_service(x_dict, y_dict, h_df , ['PNC','WDS'], path_preprocessing)
    vec_day_route_id_service_keys = list(dict_day_routeid_to_visited_custs.keys())
    # Todo
    customer_schedid_to_demand = get_demand_for_schedules(path_preprocessing)

    # loop through days and routes
    dict_day_routeid_to_loads = {}
    for vehicle, day, route_id, service in vec_day_route_id_service_keys:
        dict_visited_custs_to_demands = _get_loads_for_day_and_route_id_services(day, route_id,  vehicle, service, dict_day_routeid_to_visited_custs, y_dict, customer_schedid_to_demand)

        # we use dict_day_routeid_to_visited_custs to make sure we stick to the original order of visits
        visited_custs = dict_day_routeid_to_visited_custs[vehicle, day, route_id, service]
        demands_visited_custs = [dict_visited_custs_to_demands[c] for c in visited_custs]
        loads_visited_custs = [(visited_custs[indx], sum(demands_visited_custs[indx:])) for indx in range(len(demands_visited_custs))]
        dict_day_routeid_to_loads[vehicle, day, route_id, service] = loads_visited_custs

    return dict_day_routeid_to_loads


class ExcelIO:
    # directory refers to the general directory (e.g. "Results_FPVRPS"), not the individual folder for each scenario
    # the scenario folder might still be added

    def __init__(self, path_to_grb_result_excel):
        self.path_to_excel = path_to_grb_result_excel
        # path_to_scenario = get_path_str_for_scenario(root_directory=self.directory, scenario=self.scenario)

    # dec var names should match with names of tabs of excel file
    def get_results_from_excel_to_df(self, dec_var_names=('Z','Y','Q'), dec_var_columns=([ 'Customer', 'Vehicle', 'Day'],
                                                                                          ['O', 'D', 'Vehicle', 'Day'],
                                                                                          ['Value', 'Customer', 'Vehicle', 'Day'])):


        it_dec_var_names=iter(dec_var_names)
        dict_decvar_str_to_df = {}
        for i in range(len(dec_var_names)):
            next_var_str = it_dec_var_names.__next__()
            # print("are here")

            next_df = pd.read_excel(self.path_to_excel, sheet_name=next_var_str)
            next_df = next_df[dec_var_columns[i]]
            dict_decvar_str_to_df[dec_var_names[i]] = next_df

        return dict_decvar_str_to_df

# dict_day_routeid_to_loads = get_loads_for_day_and_route_meta(path_preprocessing, path_results)
# print("Resulting loads" , dict_day_routeid_to_loads)
#     #reader_routes = reader_routes.drop('Unnamed')
#
#     #reader_routes = reader_routes.to_dict(orient='index')
#      #print(reader_routes)


' idea: create two dataframes: '
' one with current day for route to current route id'
' and one with route id to visited customers'

# def get_loads_per_route():
#
#
#     dataframe_x_vals = stp_io.get_x(path_results)
#     selected_routes_per_day = (dataframe_x_vals[['RouteId', 'Day']]).to_dict(orient='index')
#     y_dict = stp_io.get_y(path_results)
#
#     visited_custs_d_rtd = stp_io.get_visited_customers_per_day_and_rtd(selected_routes_per_day, y_dict,
#                                                                        path_preprocessing)
#
#     pass



# mapping_dict = {'A':['a', 'b', 'c', 'd'], 'B':['aa', 'bb', 'cc']}
# updated_dict = {k: [v] for k, v in mapping_dict.items()}
# print(updated_dict)
# df = pd.DataFrame.from_dict(updated_dict, orient='index')
# print(df)
