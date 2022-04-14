# Methods for checking if routes are valid
import SETUP_and_IO as stp_io


class RouteValidation():
    def __init__(self, arc_li):
        self.valid = self.__check_all(arc_li)
        self.arc_li = arc_li

    def get_status(self):
        return self.valid

    def __check_next_link(self, indx_next_pos_arc_li, next_elem_arc_list, indx_last_pos_arc_li, arc_li):
        destination_node = next_elem_arc_list[1]

        # if we haven't reached last position in arc list but already returned to 0, the route has subtours
        if destination_node == 0 and indx_next_pos_arc_li < indx_last_pos_arc_li:
            return False
        elif destination_node == 0 and indx_next_pos_arc_li == indx_last_pos_arc_li:
            return True
        else:
            next_elem_arc_list_n = next(filter(lambda x: x[0] == destination_node, arc_li), None)
            return self.__check_next_link(indx_next_pos_arc_li + 1 , next_elem_arc_list_n, indx_last_pos_arc_li, arc_li)

    # we need a method that, given a list of arcs, removes all elements that are "chained" together
    # so we have a consumable list and a "immutable" list
    def find_route_elems_to_integrate(self, next_elem_arc_list,  arc_li_consumed, arc_list_built):
        destination_node = next_elem_arc_list[1]

        # 1 remove current element from arc_li_consumed
        arc_li_consumed.remove(next_elem_arc_list)
        arc_list_built.append(next_elem_arc_list)

        # 2 find next elem
        prev_elem = next_elem_arc_list
        next_elem_arc_list = next(filter(lambda x: x[0] == destination_node, arc_li_consumed), None)
        if next_elem_arc_list[1] == 0:
            return arc_li_consumed, arc_list_built, prev_elem
        else:
            return self.find_route_elems_to_integrate(next_elem_arc_list, arc_li_consumed, arc_list_built)

    def _aux_integrate_missing_elems(self, remaining_arc_list, arc_list_built, last_dest):

        #print("remaining arc list"  , remaining_arc_list, " built arc list ", arc_list_built)
        if len(remaining_arc_list) == 1:
            last_remaining_arc = remaining_arc_list[0]
            arc_list_built.append((last_remaining_arc[0],0))
            return arc_list_built
        elif any(filter(lambda x : x[1] == arc_list_built[-1][1],  arc_list_built[:-1])): # multiple subtours included!
            #print("are here")
            next_valid_destination = remaining_arc_list[0][0]
            last_valid_origin = arc_list_built[-1][0]
            arc_list_built[-1] = (last_valid_origin, next_valid_destination)
            return self._aux_integrate_missing_elems(remaining_arc_list, arc_list_built, next_valid_destination)
        else:
           # print("are here 2")
            # what
            next_elem_to_add = (next(filter(lambda x: x[0] == last_dest, remaining_arc_list)))
            #print(next_elem_to_add)
            remaining_arc_list.remove(next_elem_to_add)
            arc_list_built.append(next_elem_to_add)
            #print(arc_list_built)
            return self._aux_integrate_missing_elems(remaining_arc_list, arc_list_built, next_elem_to_add[1])



    def _find_main_route(self, faulty_arc_list_rest, built_arcs, next_link):
        if not next_link:
            return built_arcs, faulty_arc_list_rest
        else:
            built_arcs.append(next_link)
            if next_link in faulty_arc_list_rest: faulty_arc_list_rest.remove(next_link)
            next_link = next(filter(lambda x: x[0] == next_link[1], faulty_arc_list_rest), None)
            return self._find_main_route(faulty_arc_list_rest, built_arcs, next_link)


    def correct_faulty_routes(self):
        hub_leaving_link = next(filter(lambda x: x[0] == 0, self.arc_li), None)
        if not hub_leaving_link:
            hub_leaving_link = (0, self.arc_li[0][0]) # aux starter link (# todo why can this happen?)

        built_arcs, faulty_arc_list_rest = self._find_main_route(self.arc_li, [],  hub_leaving_link)
        if not faulty_arc_list_rest:
            return built_arcs + [(built_arcs[-1][1], 0)]
        # print("built arcs", built_arcs, " faulty_arc_list_rest", faulty_arc_list_rest)
        built_arcs[-1] = built_arcs[-1][0], faulty_arc_list_rest[0][0] # replace last destination in built list with first origin in remaining list
        final_route = self._aux_integrate_missing_elems(faulty_arc_list_rest, built_arcs, built_arcs[-1][1])
        return final_route


    # this method gets a list of links : [(0,1), (1,2), (2,5), (5,0)], (element does not have to be ordered)
    # checks if these links indicate that there are subtours within the route and returns false in this case, otherwise true
    def __check_if_route_has_no_subtours(self, arc_list):
        starter_elem_arc_list = next(filter(lambda x: x[0] == 0, arc_list), None)  # we start with arc that leaves hub
        num_arcs_in_list = len(arc_list)
        indx_last_pos_arc_li = num_arcs_in_list - 1

        return self.__check_next_link(0, starter_elem_arc_list, indx_last_pos_arc_li, arc_list)


    def __check_if_route_connected_to_hub(self, arc_list):
        starter_elem_arc_list = next(filter(lambda x: x[0] == 0, arc_list), None)
        return True if starter_elem_arc_list else False

    # Hierarchy of checks so that the tests function as intended: (usually, 1 and 2 are given and 3 has to be checked)
    # 1. check if route has valid elements
    # check if route is connected to hub
    # 3. check if route has subtours

    # second check is the subtour check then
    def __check_if_route_has_valid_elements(self, arc_li):
        only_origins = list(map(lambda x: x[0], arc_li))
        only_destins = list(map(lambda x: x[1], arc_li))

        transformed_list = [( only_origins.count(li[0]), only_destins.count(li[0])) for li in arc_li]
        #print(transformed_list)# check if each origin occurs once
        return not ( any(i != j for i, j in transformed_list)  or any(i != 1 for i, j in transformed_list))


    def __check_all(self, arc_li):
        if not arc_li:
            return True
        valid_elems =  self.__check_if_route_has_valid_elements(arc_li)
        if not valid_elems:
            return False
        else:
            if not self.__check_if_route_connected_to_hub(arc_li):
                return False
            else:
                return self.__check_if_route_has_no_subtours(arc_li)

r = RouteValidation([(0,1),(1,4),(4,5), (5,8), (8,0)])
print(r._aux_integrate_missing_elems([(14,13),(13,14),(9,10),(10,9)], [(0,1),(1,4),(4,5), (5,8), (8,14)], 14))

class FPVRPPostProcessor():

    def __init__(self, path_to_gurobi_result, scenario, cfg, dec_var_names=('Z','Y','Q'), dec_var_indices_names=([ 'Customer', 'Vehicle', 'Day'],
                                                                                          ['O', 'D', 'Vehicle', 'Day'],
                                                                                          ['Value', 'Customer', 'Vehicle', 'Day','ServiceType'])):
        self.path_to_gurobi_result = path_to_gurobi_result
        self.scenario = scenario
        self.T = cfg.T

        # default
        self.dec_var_names = dec_var_names
        self.dec_var_indices_names = dec_var_indices_names

        # automatically triggered methods
        self._read_results()
        self._convert_result_format()

    def _read_results(self):
        excelio = stp_io.ExcelIO(self.path_to_gurobi_result)
        self.dict_decvarstr_to_df = excelio.get_results_from_excel_to_df(self.dec_var_names, self.dec_var_indices_names) # default parameters are already given, correspond to tab names of excel file and the column names that are relevant

    def _convert_result_format(self):
        self._transform_df_results_to_dict()
        self._transform_y_to_dict_vehicle_day_to_arclist()
        self._transform_q_to_dict_customer_vehicle_day_to_quantity()

    def get_vehicle_day_to_route_dict(self):
        return self.vehicle_day_to_arcs

    def get_dict_decvar_to_vehicleday(self):
        return self.dict_decvarstr_to_dict_vehicleday_to_val

    def _create_next_inner_dict(self, df):

        dict_vehicleday_to_routes = {}
        for k in self.scenario.K:
            for t in (self.T):
                results = list(df.query('Vehicle ==' + str(k) + ' and Day == ' + str(t)).values.tolist())

                dict_vehicleday_to_routes[k,t] = results
        #print("Are in  next inner dict", dict_vehicleday_to_routes)
        return dict_vehicleday_to_routes

    def _transform_q_to_dict_customer_vehicle_day_to_quantity(self, relevant_tab='Q'):
        self.dict_customer_vec_day_to_q = {}
        for k, v in self.dict_decvarstr_to_dict_vehicleday_to_val[relevant_tab].items():
            # v looks like this: [[25.0, 14, 0, 0, 'PNC'], [61.8, 14, 0, 0, 'WDS'], [82.6, 15, 0, 0, 'WDS']]
            for i in v:
                vehicle, day = k
                # print(i)
                customer = i[1]
                service_type = i[4]
                self.dict_customer_vec_day_to_q[customer, vehicle, day, service_type] = i[0]  # eg, remove the other elements like (k, t)-columns

    def get_dict_customer_vec_day_to_q(self):
        return self.dict_customer_vec_day_to_q

    def _transform_y_to_dict_vehicle_day_to_arclist(self, relevant_tab='Y'):
        self.vehicle_day_to_arcs = {}
        for k, v in self.dict_decvarstr_to_dict_vehicleday_to_val[relevant_tab].items():
            # print(v)
            self.vehicle_day_to_arcs[k] = [(i[0], i[1]) for i in v] # eg, remove the other elements like (k, t)-columns

    def _transform_df_results_to_dict(self):
        self.dict_decvarstr_to_dict_vehicleday_to_val = {}
        iter_dec_var_names = iter(self.dec_var_names)
        next_df_str = next(iter_dec_var_names, None)
        while next_df_str:
            #print(next_df_str)
            self.dict_decvarstr_to_dict_vehicleday_to_val[next_df_str] = self._create_next_inner_dict(self.dict_decvarstr_to_df[next_df_str])
            next_df_str = next(iter_dec_var_names, None)

        #print(self.dict_decvarstr_to_vehicledaydict)
        return self.dict_decvarstr_to_dict_vehicleday_to_val

    def _get_faulty_routes(self, relevant_var='Y'):
        self.faulty_routes = []
        for k, v in self.dict_decvarstr_to_dict_vehicleday_to_val[relevant_var].items():
            res = RouteValidation(v).get_status()
            if not res:
                self.faulty_routes.append((k, v))
        # print("faulty routes" , self.faulty_routes)
        return self.faulty_routes


    def _get_additional_costs_through_cor_route(self, faulty_route, new_route):
        costs_old = sum([self.distances[i,j] for i,j in faulty_route])
        costs_new = sum([self.distances[i,j] for i,j in new_route])
        return  costs_new - costs_old

    def _correct_faulty_routes(self, relevant_var ='Y'):
        self.additional_distance_after_adjust = 0
        y_dict = self.vehicle_day_to_arcs
        for (k, d), route in self.faulty_routes:
            faulty_route = y_dict[k, d]
            corrected_route = RouteValidation(faulty_route).correct_faulty_routes()
            self.additional_distance_after_adjust += self._get_additional_costs_through_cor_route(faulty_route, corrected_route)
            y_dict[k, d] = corrected_route
       # print("** Done ** \n ")
        self.dict_decvarstr_to_dict_vehicleday_to_val[relevant_var] = y_dict
        #print(self.vehicle_day_to_arcs)

    def get_distance(self):
        return self.additional_distance_after_adjust

    def correct_routes(self, distances):
        self.distances = distances
        self._get_faulty_routes()
        self._correct_faulty_routes()  # 6,1 is a faulty route
        o_d_vec_day = self._convert_new_y_for_excel()
        return self.vehicle_day_to_arcs, self.additional_distance_after_adjust, o_d_vec_day


    def _convert_new_y_for_excel(self):
        # method converts the transformed y's back into a format that is suitable for storing in an excel
        o_d_vec_day = {}
        for key, arc_list in self.vehicle_day_to_arcs.items():
            v = key[0]
            day = key[1]
            for (o,d) in arc_list:
                o_d_vec_day[o,d,v,day] = 1

        return o_d_vec_day


# # Todo : All this has to go into the execution file
# scenario = scenario_creator.Scenario(7,20,100,[0,1,2,3],5)
# # path_results = stp_io.get_path_for_scenario_results_file(scenario,
# #                                                           name_file='ResultFile.xlsx', root_directory='/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/Program/Results_FPVRPS')
# start_directory = '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs'  # '/home/sshrene/theresa/2022_aCar_VRPs'
#
# path_OD_matrix = start_directory + '/GIS_Data/11-15-21_ODs.csv'
# coordinates = dp.read_coors(start_directory + '/GIS_Data/11-15-21_CoordinatesLongitudeLatitude.csv')
# #
# od_matrix_as_dict = dp.read_odmatrix(path_OD_matrix)
# od_matrix_with_distances = dict((k, od_matrix_as_dict[k][1]) for k in od_matrix_as_dict.keys())
#
# pp = FPVRPPostProcessor('/Users/theresawettig/PycharmProjects/2022_aCar_VRPs'+'/Program/Results_FPVRPS',scenario,od_matrix_with_distances)
# vehicle_day_to_arcs, additional_distance_after_adjust, o_d_vec_day = pp.read_results_and_adjust_routes()
#
# print(" + + + Are here + + + + + " )
# stp_io.save_gurobi_res_in_excel_fpvrp([o_d_vec_day], additional_distance_after_adjust, scenario, root_directory='Results_FPVRPS',
#                                       titles_keys_per_dec_var=[['O', 'D', 'Vehicle', 'Day']], output_tab_names=('Z') , from_gurobi=False)
# #check_if_route_correct([(1,2),(2,3), (3,0)])
