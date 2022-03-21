from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import os
from itertools import cycle
import SETUP_and_IO as stp_io


path_results = 'Results/Scenario_NumVec2-LBs35-UBs80/DecisionvariableValues.xlsx'
path_preprocessing = 'Results/Scenario_NumVec2-LBs35-UBs80/Preprocessing_Inputs.xlsx'

class PVRP_Vizualizer():

    def __init__(self, path_preprocessing, path_results, root_directory_for_saving, pvrp_model, multiple_services=True):
        self.scenario = pvrp_model.scenario
        self.path_results = path_results
        self.path_preprocessing = path_preprocessing
        self.path_for_saving = stp_io.get_path_str_for_scenario(self.scenario, root_directory=root_directory_for_saving)

        self.mp = pvrp_model
        self.cfg_inputs = pvrp_model.cfg

        # setup extraction of results
        self.__get_results()

        # layout
        lis = ['tan', 'dimgrey', 'peru', 'indianred', 'darkkhaki', 'blanchedalmond','palegreen','olive','goldenrod','olivedrab','firebrick','saddlebrown','teal','cadetblue','darkviolet']
        self.colors_for_routes = iter(cycle(lis)) #nice
        self.multiple_services = multiple_services


    def __get_results(self):
        self.pd_x = stp_io.get_x_df(self.path_results)
        self.pd_x = self.pd_x.drop(columns=['Value'])
        self.df_day_routeid_to_loads = stp_io.get_loads_for_day_and_route_meta(path_preprocessing=self.path_preprocessing, path_results=self.path_results)
        self.pd_h = stp_io.get_h_df(self.path_results)
        self.df_day_routeid_service_to_loads = stp_io.get_loads_for_day_route_and_service_meta(path_preprocessing=self.path_preprocessing, path_results=self.path_results)

    # creates iterator that gives the next routes for each new call
    # check whether in-build python iterator has similar function?
    def __setup_route_iterator(self):
        self.i = -1

    def get_next_day_routes_from_x(self):
        if self.i > max(list(self.pd_x['Day'])):
            return 'END'
        else:
            self.i += 1
            route_list_current_day = list(self.pd_x.query('Day == ' + str(self.i))['RouteId'])
            return route_list_current_day

    def get_next_day_routes_from_h(self):
        if self.i > max(list(self.pd_h['Day'])):
            return 'END'
        else:
            self.i += 1
            route_list_current_day = list(self.pd_h.query('Day == ' + str(self.i))['RouteId'])
            return route_list_current_day



    def __plot_routes_for_one_day(self, routes_ids_this_day):


        # basic data
        nodes_x_cors, nodes_y_cors = self.cfg_inputs.coordinates[0], self.cfg_inputs.coordinates[1]

        # basic setups

        # get all info the next day to print
        this_day = self.i
        self.key_route_nodes = dict((r, stp_io.get_nodes_per_route(r, self.path_preprocessing)) for r in routes_ids_this_day)
        self.key_route_values_arcs = dict((r, list(zip(self.key_route_nodes[r], self.key_route_nodes[r][1:]))) for r in routes_ids_this_day)
        # #
        # go through routes of current day
        for next_route_id in list(self.key_route_values_arcs.keys()):
            color = next(self.colors_for_routes)

            next_arcs = self.key_route_values_arcs[next_route_id]


            # #
        # 1. go through all arcs of current route, draw link
            for (i,j) in next_arcs:

                plt.plot([nodes_x_cors[i], nodes_x_cors[j]], [nodes_y_cors[i], nodes_y_cors[j]], c=color, alpha=1, linestyle='dotted')

            # write down load amounts
            if not self.multiple_services: self.__plot_text_loads_one_service(this_day, next_route_id)
            else: self.__plot_text_loads_multiple_services(this_day, next_route_id)



    def __plot_text_loads_one_service(self, this_day, next_route_id):
        additional_margin = {'PNC': 0.04, 'WDS': 0}

        nodes_x_cors, nodes_y_cors = self.cfg_inputs.coordinates[0], self.cfg_inputs.coordinates[1]
        for node, load in self.df_day_routeid_to_loads[
            this_day, next_route_id]:  # list of type: [(6, 22.5), (22, 7.5)], where first tuple element is the node number and second is the remaining inbound
            # list_of_visited_nodes = self.key_route_nodes[next_route_id]
            # nodes_predecessor = list_of_visited_nodes[list_of_visited_nodes.index(node) - 1]
            x_cor = nodes_x_cors[node]  # min(nodes_x_cors[node], nodes_x_cors[nodes_predecessor]) + abs(nodes_x_cors[node] - nodes_x_cors[nodes_predecessor]) / 2
            y_cor = nodes_y_cors[node]  # min(nodes_y_cors[node], nodes_y_cors[nodes_predecessor]) + abs(nodes_y_cors[node] - nodes_y_cors[nodes_predecessor]) / 2

            # plot inbound load (to j)
            plt.text(x_cor + additional_margin['PNC'], y_cor, s='l : ' + str(round(load)), c='black', alpha=1)

    def __plot_text_loads_multiple_services(self, this_day, next_route_id):
        services = self.cfg_inputs.S
        line_break = -0.016
        line_no = 0
        horizontal_element = 0
        horizontal_gap = 0.06
        entry_made = False

        nodes_x_cors, nodes_y_cors = self.cfg_inputs.coordinates[0], self.cfg_inputs.coordinates[1]
        for v in range((len(self.mp.V))):
            for s in range(len(services)):
                if (v, this_day, next_route_id, self.cfg_inputs.S[s]) in self.df_day_routeid_service_to_loads:
                    for node, load in self.df_day_routeid_service_to_loads[v, this_day, next_route_id, self.cfg_inputs.S[s]]:  # list of type: [(6, 22.5), (22, 7.5)], where first tuple element is the node number and second is the remaining inbound
                        x_cor = nodes_x_cors[node]  # min(nodes_x_cors[node], nodes_x_cors[nodes_predecessor]) + abs(nodes_x_cors[node] - nodes_x_cors[nodes_predecessor]) / 2
                        y_cor = nodes_y_cors[node]  # min(nodes_y_cors[node], nodes_y_cors[nodes_predecessor]) + abs(nodes_y_cors[node] - nodes_y_cors[nodes_predecessor]) / 2
                        if horizontal_element == 0:
                            plt.text(x_cor + 0.01 + horizontal_element * horizontal_gap, y_cor + line_no * line_break, s='v ' +str(v)+ ' ' + str(self.cfg_inputs.S[s]) + ': ' + str(int(round(load))), c='black', alpha=0.7, fontsize=8)
                        else:
                            plt.text(x_cor + 0.01 + horizontal_element * horizontal_gap, y_cor + line_no * line_break, s='|' + str(self.cfg_inputs.S[s]) + ': ' + str(int(round(load))), c='black', alpha=0.7, fontsize=8)
                        entry_made = True
                horizontal_element += 1
            line_no += 1 if entry_made else 0
            entry_made = False
            horizontal_element = 0

    def __plot_hubs_and_customers(self):

        nodes_x_cors, nodes_y_cors = self.cfg_inputs.coordinates[0], self.cfg_inputs.coordinates[1]

        self.hub, = plt.plot(nodes_x_cors[0], nodes_y_cors[0], c='black', marker='H', label='Hub')  # draw the hub

        self.all_customers = plt.scatter(nodes_x_cors[1:], nodes_y_cors[1:], c='grey', alpha=0.6, label='Customer') # draw all customers (active + inactive)

        self.active_customers = plt.scatter([nodes_x_cors[i] for i in self.mp.scenario.C],
                                       [nodes_y_cors[i] for i in self.mp.scenario.C], marker='o', c='C1', label='Active Customers') # active customers

        for c in self.mp.C:
            plt.text(self.cfg_inputs.coordinates[0][c] + 0.005, self.cfg_inputs.coordinates[1][c], s='C ' + str(c),
                     c='C1')

    def __plot_legend_and_labels(self):
        ##
        # labels
        plt.xlabel('xcoord (long.)')
        plt.ylabel('ycoord (lat.)')

        ##
        # legend
        self.workaround_q, = plt.plot([], [], ' ', label="q: Number of provided Services")
        legend_elements = [Line2D([0], [0], color='sienna', lw=2, label='Route', linestyle='dotted')]
        handles = [self.all_customers, self.active_customers, self.hub, self.workaround_q] + legend_elements
        plt.legend(handles=handles)

    def __save_and_clear(self):

        plot_dir = os.path.dirname(__file__)

        results_dir = os.path.join(plot_dir, self.path_for_saving)
        sample_plot_name = "PVRP_Day-" + str(self.i)

        if not os.path.isdir(results_dir):
            os.makedirs(results_dir)

        # plt.gca().invert_xaxis()
        plt.savefig(results_dir + sample_plot_name)
        plt.clf()

    def plot_routes(self, method_for_getting_routes):
        # If we want to plot the multiple services scenario, we use the decision var h to paint the routes, otherwise x
        # Hence, the user has to specify (in the parameters) which object method should be used, for example: vizualizer.get_next_day_routes_from_h

        self.__setup_route_iterator()
        routes_next_day = method_for_getting_routes()
        while routes_next_day != 'END':

            plt.figure(figsize=(12, 8), dpi=80)
            self.__plot_hubs_and_customers()
            self.__plot_routes_for_one_day(routes_next_day)
            self.__plot_legend_and_labels()
            self.__save_and_clear()

            routes_next_day = method_for_getting_routes()







#
# def plot_meta_result_per_vec_num(customer_shares_list, range_setting_list, results, vehicles, filename_output):
#     print(range_setting_list)
#     print(customer_shares_list)
#
#
#     x_coordinates_of_bars = [i for i in range (len(customer_shares_list))]
#     label_ticks = list(map(lambda x: str(x), range_setting_list))
#     #plt.bar(x_coordinates_of_bars, results, width=0.9, tick_label=customer_shares_list)
#
#     plt.figure(num=3, figsize=(10, 7.5))
#
#     colors = iter(['C1','C2','C0','C4','C5'])
#     style = iter(['--','-','-.',':','--'])
#     tickstyle = iter([4,5,6,7,1,0])
#
#     i = 0
#     for v in vehicles:
#         elem = next(colors)
#         linestyle = next(style)
#         tick = next(tickstyle)
#         plt.plot(customer_shares_list, results[v], color=elem, marker=tick, linestyle=linestyle, linewidth='1.5', label='# vehicles: '+str(v), alpha=1-i)
#         i += 0.008
#
#
#     # ticks + grid
#     plt.minorticks_on()
#     plt.grid(True, axis='x', which='minor', alpha=0.3)
#     plt.grid(True, axis='y', which='minor', alpha=0.3)
#     plt.grid(True, axis='y', which='major', alpha=0.8)
#     plt.grid(True, axis='x', which='major', alpha=0.8)
#
#     plt.xlabel('Covered Population')
#     plt.ylabel('Total transportation distance in 60 days')
#
#     plt.legend(loc='best')
#
#     # save results
#     plot_dir = os.path.dirname(__file__)
#     results_dir = os.path.join(plot_dir,
#                                'Results/')
#     sample_plot_name = filename_output
#
#
#     if not os.path.isdir(results_dir):
#         os.makedirs(results_dir)
#
#     # plt.gca().invert_xaxis()
#
#     plt.savefig(results_dir + sample_plot_name)
#     plt.clf()
#



#
# def create_plots_for_vehicles(vehicles, path, filepath_to_read):
#     pd_df = read_excel_row_for_given_vec_number(filepath_to_read)
#
#
#     results_list = {}
#     for v in vehicles:
#         tiny_df = pd_df.loc[(slice(None), slice(None), slice(None), v),:]  # retrieves the relevant part of pd dataframe for that customer
#         results = list(map(lambda x: None if x == '-' else x, tiny_df['TotalDist']))
#         results_list[v] = results
#
#     list_range_values_lb  = list(map(lambda x: str(x),tiny_df.index.get_level_values(0)))
#     list_range_values_ub = list(map(lambda x: str(x),tiny_df.index.get_level_values(1)))
#     list_share_cust_vals = list(tiny_df.index.get_level_values(2))
#
#     plot_meta_result_per_vec_num(customer_shares_list=list_share_cust_vals,
#                                  range_setting_list=list_range_values_ub,
#                                  results=results_list, vehicles=vehicles, filename_output=filename_output)
#
#     results_dir = os.path.join(plot_dir, path + '/Scenario vehicle-' + str(VRP_obj.sets.K) + '_LBs-' + str(
#         VRP_obj.sets.limit[0]) + '/')


def paint_output(VRP_obj, dataframes, path):
    # # add arcs_list to plot
    active_times_arcs_list = dict(
        (t, (i, j)) for (i, j) in VRP_obj.sets.A for t in VRP_obj.sets.T if VRP_obj.y[i, j, t].x > 0.99)
    # plot result for each time slot
    for t in VRP_obj.sets.T:
        xc = VRP_obj.sets.coordinates[0]
        yc = VRP_obj.sets.coordinates[1]
        y_results = dataframes['y']
        q_results = dataframes['q']
        l_results = dataframes['l']

        plt.figure(figsize=(12, 8), dpi=80)
        # # plot the hub
        hub, = plt.plot(VRP_obj.sets.coordinates[0][0], VRP_obj.sets.coordinates[1][0], c='r', marker='s', label='Hub')
        # # plot the clients (highlight in green if not all considered)
        all_customers = plt.scatter(xc[1:], yc[1:], c='grey', alpha=0.5, label='Customer')
        workaround_q, = plt.plot([], [], ' ', label="q: Number of provided Services")

        # plot active customers
        active_x_coordinates = [xc[i] for i in VRP_obj.sets.C]
        active_y_coordinates = [yc[i] for i in VRP_obj.sets.C]

        active_customers = plt.scatter(active_x_coordinates, active_y_coordinates, c='g', label='Active Customers')

        # plot used arcs (y == 1):
        set_colours = {'PNC':'magenta', 'WDS':'darkslateblue'}
        labels =  {'PNC':'PNC', 'WDS':'WDS'}
        line_styles = {'PNC': 'dotted', 'WDS': (0,(1,10))}


        # Create the figure
        additional_margin = {'PNC': 0.04 , 'WDS': 0}
        for s in (VRP_obj.sets.S):
            margin = 0
            for a in range(len(VRP_obj.sets.A)):
                i, j = VRP_obj.sets.A[a]

                if int(y_results.loc[(i,j,t),:].item()) > 0.5:
                    plt.plot([xc[i], xc[j]], [yc[i], yc[j]], c='sienna', alpha=0.9, linestyle='dotted')  # painting the route (arc)

                    # retrieve load
                    load = round(float(l_results.loc[(i, j, t, s), :].item()))

                    if j != 0:
                        x_coor = min (xc[i], xc[j]) + abs(xc[i] - xc[j])/2 + 0.03
                        y_coor = min (yc[i], yc[j]) + abs(yc[i] - yc[j])/2
                        plt.text(x_coor + additional_margin[s], y_coor, s='l : ' + str(load), c=set_colours[s], alpha=1)


        # plot number of services
        for c in range(len(VRP_obj.sets.C)):

            # q_value = round(float(q_results.loc[(VRP_obj.sets.C[c],t, 'PNC'),:].item()))
            #
            # if q_value != 0:
            #     plt.text(xc[VRP_obj.sets.C[c]] + 0.03, yc[VRP_obj.sets.C[c]], s='q: ' + str(q_value))

            plt.text(xc[VRP_obj.sets.C[c]]+0.005, yc[VRP_obj.sets.C[c]], s='C ' + str(VRP_obj.sets.C[c]),
                     c='green')



        legend_elements = [Line2D([0], [0], color='sienna', lw=2, label='Route', linestyle='dotted')]

        plt.xlabel('xcoord (long.)')
        plt.ylabel('ycoord (lat.)')
        handles = [all_customers, active_customers, hub, workaround_q] + legend_elements
        plt.legend(handles=handles)

        plot_dir = os.path.dirname(__file__)
        results_dir = os.path.join(plot_dir, path+ '/Scenario vehicle-'+str(VRP_obj.sets.K)+'_LBs-'+str(VRP_obj.sets.limit[0]) +'/')
        sample_plot_name = "Plot_VRP_" + str(t)

        if not os.path.isdir(results_dir):
            os.makedirs(results_dir)

        #plt.gca().invert_xaxis()
        plt.savefig(results_dir  + sample_plot_name)
        plt.clf()
