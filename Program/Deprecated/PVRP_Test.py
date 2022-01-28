import pandas as pd
from Program.Deprecated import SETUP_and_IO as stp_io

path_results = '../Results/Scenario_NumVec2-LBs35-UBs80/DecisionvariableValues.xlsx'
path_preprocessing = '../Results/Scenario_NumVec2-LBs35-UBs80/Preprocessing_Inputs.xlsx'


def check_capacity_constr(visited_customers_per_day_and_rtd, capacity, y, path_preprocessing):
    xlsxwriter = pd.ExcelWriter(path_preprocessing, engine='xlsxwriter')
    df = pd.read_excel(xlsxwriter, sheet_name='DemandsForSchedules')
    df = df.set_index(['CustomerId','ScheduleId'])
    df.drop(columns=['Unnamed: 0'], inplace=True)
    #print(df.query('CustomerId == '+str(1)+' and ScheduleId == '+str(3))['PNC'])


    for k, v in visited_customers_per_day_and_rtd.items():
        visited_cst = v
        amount = sum((lambda l: (df.query('CustomerId == '+str(l)+' and ScheduleId == '+str(y[l]))['PNC']).values)(i) for i in visited_cst)

        print("Max. capacity: ", capacity, " Amount:  ", amount)




stp_io.get_days_in_schedule(19, path_preprocessing)

dataframe_x_vals = stp_io.get_x_df(path_results)
selected_routes_per_day = (dataframe_x_vals[['RouteId','Day']]).to_dict(orient='index')
y_dict = stp_io.get_y(path_results)

visited_custs_d_rtd = stp_io.get_visited_customers_per_day_and_rtd(selected_routes_per_day, y_dict, path_preprocessing)
check_capacity_constr(visited_custs_d_rtd , 0, y_dict, path_preprocessing)


#
# print(get_visited_customers_per_day_and_rtd(selected_routes_per_day, y_dict))







