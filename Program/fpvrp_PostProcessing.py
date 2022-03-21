# Methods for checking if routes are valid
from itertools import product
import numpy as np
import pandas as pd
from k_opt_heuristics import tsp_2_opt

index_hub = 100


class RouteValidation():
    def __init__(self, arc_li):
        self.valid = self.__check_all(arc_li)
        self.arc_li = arc_li

    def order_links(self):
        print("arclist unordered : ", self.arc_li)
        arclist_ordered = []
        current_elem = self.arc_li[0]
        arclist_ordered.append(current_elem)
        for count in range(len(self.arc_li) - 1):
            destination = current_elem[1]
            current_elem = [i for i in self.arc_li if i[0] == destination][0]  # next element: origin = current dest
            arclist_ordered.append(current_elem)
        print("arclist ordered ", arclist_ordered)
        return arclist_ordered




    def get_status(self):
        return self.valid

    def __check_next_link(self, indx_next_pos_arc_li, next_elem_arc_list, indx_last_pos_arc_li, arc_li):
        destination_node = next_elem_arc_list[1]

        # if we haven't reached last position in arc list but already returned to 0, the route has subtours
        if destination_node ==  index_hub and indx_next_pos_arc_li < indx_last_pos_arc_li:
            return False
        elif destination_node ==  index_hub and indx_next_pos_arc_li == indx_last_pos_arc_li:
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
        if next_elem_arc_list[1] ==  index_hub:
            return arc_li_consumed, arc_list_built, prev_elem
        else:
            return self.find_route_elems_to_integrate(next_elem_arc_list, arc_li_consumed, arc_list_built)


    def _aux_integrate_missing_elems(self, remaining_arc_list, arc_list_built, last_dest):

        #print("remaining arc list"  , remaining_arc_list, " built arc list ", arc_list_built)
        if len(remaining_arc_list) == 1:
            last_remaining_arc = remaining_arc_list[0]
            arc_list_built.append((last_remaining_arc[0],  index_hub))
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
            # print("HERE WITH ", faulty_arc_list_rest,  "built arcs " , built_arcs, "next elem to add: ", next_link)
            if next_link in faulty_arc_list_rest: faulty_arc_list_rest.remove(next_link)
            next_link = next(filter(lambda x: x[0] == next_link[1], faulty_arc_list_rest), None)
            # print("Next link: ", next_link)
            return self._find_main_route(faulty_arc_list_rest, built_arcs, next_link)


    def correct_faulty_routes(self):
        hub_leaving_link = next(filter(lambda x: x[0] ==  index_hub, self.arc_li), None)
        if not hub_leaving_link:
            hub_leaving_link = ( index_hub, self.arc_li[0][0]) # aux starter link (# todo why can this happen?)

        built_arcs, faulty_arc_list_rest = self._find_main_route(self.arc_li, [],  hub_leaving_link)
        if not faulty_arc_list_rest:
            return built_arcs + [(built_arcs[-1][1],  index_hub)]
        # print("built arcs", built_arcs, " faulty_arc_list_rest", faulty_arc_list_rest)
        built_arcs[-1] = built_arcs[-1][0], faulty_arc_list_rest[0][0] # replace last destination in built list with first origin in remaining list
        corrected_route = self._aux_integrate_missing_elems(faulty_arc_list_rest, built_arcs, built_arcs[-1][1])
        return corrected_route

    # this method gets a list of links : [(0,1), (1,2), (2,5), (5,0)], (element does not have to be ordered)
    # checks if these links indicate that there are subtours within the route and returns false in this case, otherwise true
    def __check_if_route_has_no_subtours(self, arc_list):
        starter_elem_arc_list = next(filter(lambda x: x[0] ==  index_hub, arc_list), None)  # we start with arc that leaves hub
        num_arcs_in_list = len(arc_list)
        indx_last_pos_arc_li = num_arcs_in_list - 1

        return self.__check_next_link(0, starter_elem_arc_list, indx_last_pos_arc_li, arc_list)

    def __check_if_route_connected_to_hub(self, arc_list):
        starter_elem_arc_list = next(filter(lambda x: x[0] ==  index_hub, arc_list), None)
        return True if starter_elem_arc_list else False


    # Hierarchy of checks so that the tests function as intended: (usually, 1 and 2 are given and 3 has to be checked)
    # 1. check if route has valid elements
    # check if route is connected to hub
    # 3. check if route has subtours

    # second check is the subtour check then
    def __check_if_route_has_valid_elements(self, arc_li):
        only_origins = list(map(lambda x: x[0], arc_li))
        only_destins = list(map(lambda x: x[1], arc_li))

        transformed_list = [(only_origins.count(li[0]), only_destins.count(li[0])) for li in arc_li]
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


class FPVRPPostProcessor():
                                        # excel io grb results have MULTIINDEX!
    def __init__(self, cfg, scenario, excel_io_grb_results, distances):
       # self.path_to_gurobi_result = excel_io.get_path_to_excel_file()
        self.scenario = scenario
        self.T = cfg.T
        self.grb_results_dict_to_df_input = excel_io_grb_results.copy()
        self.distances = distances

                                        # automatically triggered methods

    def _find_and_set_faulty_routes(self, grb_results_dict_to_df_input_y):

        df_y = grb_results_dict_to_df_input_y
        faulty_routes = {}
        for (k, d) in product(self.scenario.K, self.T):
            try:
                my_index = (slice(None), slice(None), k, d)
                df_sub = df_y.loc[(my_index),:]

                # returns: [(1, 0, 11, 4), (12, 44, 11, 4),,. (o, d, v, d) ...
                indices_o_d_vehicle_day = df_sub.index.values.tolist()

                # only takes the first two elements of each tuple element
                arcs_for_vehicle_day = [(orig,dest) for orig, dest, veh, day in indices_o_d_vehicle_day]
                print(arcs_for_vehicle_day)
                route_is_valid = RouteValidation(arcs_for_vehicle_day).get_status()
                if not route_is_valid:
                    faulty_routes[k, d] = arcs_for_vehicle_day

            except KeyError:
                pass
        return faulty_routes

    def _get_cost_difference(self, faulty_route, new_route):

        costs_old = sum([self.distances[i,j] for i,j in faulty_route])
        costs_new = sum([self.distances[i,j] for i,j in new_route])
        return  costs_new - costs_old

    def correct_routes(self, grb_results_dict_to_df_input_y, relevant_var ='Y'):

        # #
        # use given distances and find faulty routes
        faulty_routes = self._find_and_set_faulty_routes(grb_results_dict_to_df_input_y.copy())
        print("faulty routes: ", faulty_routes)

        #
        self.additional_distance_after_adjust = 0
        grb_y_df_copy_without_mltindex = grb_results_dict_to_df_input_y.copy().reset_index()

        for (k, d), faulty_route in faulty_routes.items():

            # #
            # get corrected route for current faulty route
            corrected_route = RouteValidation(faulty_route).correct_faulty_routes()
            self.additional_distance_after_adjust += self._get_cost_difference(faulty_route,
                                                                               corrected_route)
            corrected_route_iter = iter(corrected_route)

            # #
            # index list
            ind_list = grb_y_df_copy_without_mltindex.index[(grb_y_df_copy_without_mltindex['Vehicle'] == k) &
                                                            (grb_y_df_copy_without_mltindex['Day'] == d)].tolist()

            for i in ind_list:
                next_link = corrected_route_iter.__next__()
                grb_y_df_copy_without_mltindex.loc[i] = [next_link[0], next_link[1], k, d, 1]

        return grb_y_df_copy_without_mltindex

    def get_distance(self):
        return self.additional_distance_after_adjust


    def _enhance_routes_aux(self, arclist_current_route):
        print("INPUT ROUTE TO BE IMPROVED" , arclist_current_route)

        # #
        # preparations : map nodes in given route to new indices (0, .. , n) so the k-opt methods can be applied
        nodes_in_tour = [i[0] for i in RouteValidation(arclist_current_route).order_links()]
        node_id_old_to_new = dict((nodes_in_tour[i], i) for i in range(len(nodes_in_tour)))
        node_id_new_to_old = dict((i, nodes_in_tour[i]) for i in range(len(nodes_in_tour)))

        # #
        # create o-d matrix with new indices
        distances_mapped = dict(((node_id_old_to_new[o], node_id_old_to_new[d]), self.distances[o,d])
                                for o,d in product(nodes_in_tour, nodes_in_tour) if o != d)

        # #
        # prepare the input parameters for tsp_2_opt method (graph &  list of used nodes)
        graph = np.array([[distances_mapped[i, i_2] if i_2 != i else 0 for i_2 in node_id_old_to_new.values()]
                          for i in node_id_old_to_new.values()])
        arclist_current_route_mapped = [node_id_old_to_new[i] for i in nodes_in_tour] + [node_id_old_to_new[nodes_in_tour[0]]]
        # #
        # use heuristic
        best_found_route_single_nodes = tsp_2_opt(graph, arclist_current_route_mapped)

        # #
        # mapping back to original node indices
        best_found_route_links = list(map(
            (lambda x: (node_id_new_to_old[x[0]], node_id_new_to_old[x[1]])), zip(best_found_route_single_nodes, best_found_route_single_nodes[1:])))
        print("OUTPUT ", best_found_route_links)
        return best_found_route_links

    # gets dictionary with o-d distances and route_df as multiindex pd dataframe
    def enhance_routes(self, routes_df):

        df_y_with_multiindex = routes_df.copy()
        df_y_modified = routes_df.copy().reset_index()

        self.additional_distance_after_adjust = 0

        for (k, d) in product(self.scenario.K, self.T):

            entry_available = True
            try:
                my_indices = (slice(None), slice(None), k, d)
                df_sub = df_y_with_multiindex.loc[(my_indices),:]


            except KeyError:
                entry_available = False
                pass

            if entry_available:

                # returns: [(1, 0, 11, 4), (12, 44, 11, 4),,. (o, d, v, d) ...
                indices_o_d_vehicle_day = df_sub.index.values.tolist()

                # only takes the first two elements of each tuple element
                links_for_k_d = [(orig, dest) for orig, dest, veh, day in indices_o_d_vehicle_day]

                links_for_k_d_impr = self._enhance_routes_aux(links_for_k_d)
                links_for_k_d_impr_it = iter(links_for_k_d_impr)

                self.additional_distance_after_adjust += self._get_cost_difference(links_for_k_d,
                                                                                   links_for_k_d_impr)

                # #
                # index list
                ind_list = df_y_modified.index[ (df_y_modified['Vehicle'] == k) & (df_y_modified['Day'] == d)].tolist()

                for i in list(ind_list):
                    print(i)
                    next_link = links_for_k_d_impr_it.__next__()
                    df_y_modified.loc[i] = [next_link[0], next_link[1], k, d, 1]

        return df_y_modified

    def set_multiindex_for_y_df(self, df, indices=('O','D','Vehicle','Day')):
        return df.set_index(list(indices))



