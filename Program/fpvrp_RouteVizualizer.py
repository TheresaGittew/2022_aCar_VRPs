from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import os
from itertools import cycle
import ExcelHandler as stp_io

index_hub = 100

class PVRP_Vizualizer():

    def __init__(self, framework_input, scenario, dicts_to_grb_dataframes_with_multiindex, root_directory_for_saving):
        self.scenario = scenario
        self.path_for_saving = root_directory_for_saving
        self.max_days = len(framework_input.T)
        self.framework_input = framework_input
        self.dicts_to_grb_dataframes_with_multiindex = dicts_to_grb_dataframes_with_multiindex

        # #
        # Layout settings
        lis_colors = ['tan', 'dimgrey', 'peru', 'indianred', 'darkkhaki', 'olive','goldenrod','olivedrab','firebrick',
                      'saddlebrown','teal','cadetblue','darkviolet']
        lis_colors_services = iter(cycle(['green', 'navy','crimson','darkorange']))
        self.colors_for_routes = iter(cycle(lis_colors))
        self.colors_for_services = dict((s, next(lis_colors_services)) for s in self.framework_input.S)


        self.init_and_assign_decvars()


    def init_and_assign_decvars(self):
        self.y = self.dicts_to_grb_dataframes_with_multiindex['Y']
        self.q = self.dicts_to_grb_dataframes_with_multiindex['Q']
        # print("Q results" , self.q_results)

    def __setup_route_iterator(self, max_days):
        self.day_iter = -1
        self.max_days = max_days

    def _get_dict_vehicle_to_routes_for_current_day(self):
        if self.day_iter == self.max_days - 1: return 'END'
        else:
            self.day_iter += 1
            my_index = (slice(None), slice(None), slice(None), self.day_iter)
            df_sub = self.y.loc[(my_index), :]

            # returns: [(1, 0, 11, 4), (12, 44, 11, 4),,. (or, dest, vec, day) ...
            indices_o_d_vehicle_day = df_sub.index.values.tolist()
            print(indices_o_d_vehicle_day)

            # only takes the first two elements of each tuple element
            # returns: {11: (0,1), 11: (1,14), 11: (14, 18), ..}
            dict_vehicle_to_routes_current_day = dict((veh, list(map(lambda x2: (x2[0], x2[1]),
                                                                     filter(lambda x: x[2] == veh, indices_o_d_vehicle_day)))) for (orig, dest, veh, day) in indices_o_d_vehicle_day)
            print(dict_vehicle_to_routes_current_day)
            return dict_vehicle_to_routes_current_day

    def _write_q(self, x_cor, y_cor,  i, k):
        horizontal_space = 0

        for s in self.framework_input.S:
            entry_available = True

            print("next s: ", s)
            try:
                q = self.q.loc[i, k, self.day_iter, s]
            except KeyError:
                #print("Are in key error for customer, k, day, s: ", i, k, self.day_iter, s)

                entry_available = False
            if entry_available:
                plt.text(x_cor + 0.3, y_cor + horizontal_space, s=str(s) + ': ' + str(int(q)),
                         c=self.colors_for_services[s],
                         alpha=1, fontsize=10)
                horizontal_space -= 0.3  # 0.03


    def _plot_routes_for_one_day(self, vehicle_to_routes_current_day):
        # basic data
        nodes_x_cors, nodes_y_cors = self.framework_input.coordinates[0], self.framework_input.coordinates[1]
        # get all info the next day to print
        this_day = self.day_iter
        for vehicle, route in vehicle_to_routes_current_day.items():
            print("We are here on day" , self.day_iter, " with vehicle " , vehicle , " and route ", route)

            color = next(self.colors_for_routes)
            for (i, j) in route:

                # #
                # 1: Draw the link
                plt.plot([nodes_x_cors[i], nodes_x_cors[j]], [nodes_y_cors[i], nodes_y_cors[j]], c=color, linestyle='dotted')
                if i == 0:
                    plt.text((nodes_x_cors[j] // 2) + 0.01, (nodes_y_cors[j] / 2) + 0.01, s=' vehcl: ' +str(vehicle), c=color)

                # #
                # 2: Write down the transported quantity per service type
                #
                print("next customer : " , i)
                self._write_q(nodes_x_cors[i], nodes_y_cors[i],  i, vehicle)
                # #

    def __plot_hubs_and_customers(self):

        nodes_x_cors, nodes_y_cors = self.framework_input.coordinates[0], self.framework_input.coordinates[1]

        self.hub, = plt.plot(nodes_x_cors[index_hub], nodes_y_cors[index_hub], c='black', marker='H', label='Hub')  # draw the hub

        self.all_customers = plt.scatter([nodes_x_cors[i] for i in list(nodes_x_cors.keys())],
                                          [nodes_y_cors[i] for i in list(nodes_y_cors.keys())], c='grey', alpha=0.6, label='Customer') # draw all customers (active + inactive)

        self.active_customers = plt.scatter([nodes_x_cors[i] for i in self.scenario.C],
                                            [nodes_y_cors[i] for i in self.scenario.C], marker='o', c='C1', label='Active Customers') # active customers

        for c in self.scenario.C:
            plt.text(self.framework_input.coordinates[0][c] + 0.005, self.framework_input.coordinates[1][c], s='C ' + str(c),
                     c='C1')

        plt.scatter([10,0],[10,0], c='white')

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
        sample_plot_name = "PVRP_Day-" + str(self.day_iter)

        if not os.path.isdir(results_dir):
            os.makedirs(results_dir)

        # plt.gca().invert_xaxis()
        plt.savefig(results_dir + sample_plot_name)
        plt.clf()

    def plot_active_cust(self):
        self.__setup_route_iterator(len(self.framework_input.T))
        plt.figure(figsize=(12, 8), dpi=80)
        self.__plot_hubs_and_customers()
        self.__plot_legend_and_labels()
        self.__save_and_clear()

    def plot_routes(self):


        self.__setup_route_iterator(len(self.framework_input.T))

        vehicle_routes_for_current_day = self._get_dict_vehicle_to_routes_for_current_day()

        while vehicle_routes_for_current_day != 'END':

            plt.figure(figsize=(12, 8), dpi=80)
            self.__plot_hubs_and_customers()
            self._plot_routes_for_one_day(vehicle_routes_for_current_day)
            self.__plot_legend_and_labels()
            self.__save_and_clear()

            vehicle_routes_for_current_day = self._get_dict_vehicle_to_routes_for_current_day()








#
#
#


