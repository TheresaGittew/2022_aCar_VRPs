import DEPR_ReadNilsInputFiles as dp
from itertools import permutations, product, combinations
import random
import pandas as pd

# permutations: order counts; combinations: order does not matter

# Pre-Processing:
# required input parameters
# set of routes R, where each route must start and end at the depot
# set of combinations, where one combination i p (question: each combination is unique for each user or in general ?)
# each feasible combinations per customer (dictionary)
# a: also given, matching customers with one possible route
# b : also given, telling whether day t is in combination p
# sets per route: E(r), N(r) => hand in route index, get back a number of arcs: E_r
# m : Number of vehicles available every day


# a[i,r] => 1 if customer i is visited by route r, 0 otherwise
# b[p,t] => 1 if day t is in combination p, 0 otherwise


# Todo : Replace this block by functions that are triggered in InputReader() Class and the results should
# Todo: returned to InputReader() class


# We need:
# - user specific demand
# Weitere Funktion, die sich total_demand_nested_dict nimmt (d.h. gesamtnachfrage für gesamten Zeitraum), und für jedes Pattern ermittelt,
# Welche tägliche Nachfrage daraus resultieren würde.


# all schedules is a dictionary that is structured like this:
#   { 1 : [1,2,3,4], 2: [4,8,9], 3: ... }
def create_all_schedules(number_of_days):
    all_patterns = {}
    l = [i for i in range(number_of_days)]
    schedule_id = 0
    for num_allowed_days in range(1,number_of_days):
        combis_visits = combinations(l, num_allowed_days)
        for c in combis_visits:
            all_patterns[schedule_id] = list(c)

            schedule_id += 1
    return all_patterns


# b => 'artificial parameter', 1 if a particular day is included in a schedule;
#                              0 otherwise
def create_b_p_t(all_schedules, T):
    b_p_t = {}
    for k, v in all_schedules.items():
        for t in T:
            b_p_t[k,t] = 1 if t in v else 0
    return b_p_t


# returns C_p as a dict, where a random element of the dict P gets selected
def find_schedules_for_each_customer(all_schedules_keys, customers):
    C_p = {}
    f = {}

    # allowed_schedules_test = { customers[0]: [0,6, 37, 48], customers[1]:[1,6,46, 57 ], customers[2]:[2,7, 30, 40],
    #                            customers[3]: [3, 19, 32, 55],
    #                            customers[4]: [4,20, 39, 42] , customers[5]: [5, 17, 35, 40],
    #                            customers[6]: [17, 19, 44, 50], customers[7]:[20, 15, 29, 37]}

    for c in customers:
        random.seed(c)
        C_p[c] = [random.randint(0, max(all_schedules_keys)) for i in range(5)]
        #C_p[c] = allowed_schedules_test[c]

    # for p in all_schedules_keys:
    #     for c in customers:
    #         f[c,p] = 1 if p in C_p[c] else 0

    return C_p

def find_schedules_for_each_customer_and_service(all_schedules_keys, customers, services):
    def convert_fromat_C_ps(C_ps):
        C_ps_converted_for_df = {}
        for keys in list(C_ps.keys()):
            C_ps_converted_for_df[keys] = {schedule_index: C_ps[keys][schedule_index] for schedule_index in
                                           range(len(C_ps[keys]))}
        return C_ps_converted_for_df

    C_p = {}
    f = {}

    # allowed_schedules_test = { customers[0]: [0,6, 37, 48], customers[1]:[1,6,46, 57 ], customers[2]:[2,7, 30, 40],
    #                            customers[3]: [3, 19, 32, 55],
    #                            customers[4]: [4,20, 39, 42] , customers[5]: [5, 17, 35, 40],
    #                            customers[6]: [17, 19, 44, 50], customers[7]:[20, 15, 29, 37]}

    for c in customers:
        for s in services:
            random.seed(c )# random.seed(c * services.index(s))
            C_p[c,s] = [random.randint(0, max(all_schedules_keys)) for i in range(15)]
            #C_p[c] = allowed_schedules_test[c]
    return convert_fromat_C_ps(C_p)

# creates "dict_all_routes", which is a dictionary containing route_ids as keys and a list as value.
# the list contains an order of nodes, describing the order of visited notes in the route
def find_all_routes(customer_nodes, od_matrix, max_nodes_per_route=4, threshold_max_length=200):
    dict_all_routes = {}
    list_lens_of_routes = {}
    route_id = 0

    # step 1: find all subsets of nodes according to given max_nodes_per_route
    all_node_combs = [item for lis in [combinations(customer_nodes, i) for i in range(1, max_nodes_per_route)] for item in lis]
    for i in all_node_combs:
        permutations_per_subset = permutations(i) # create different permutations for each set of customers (meaning, different path combinations)

        for p in permutations_per_subset:
            list_of_nodes = [0] + list(p)
            #print(list_of_nodes)

            zipped_lists = list(zip(list_of_nodes, list_of_nodes[1:] + [list_of_nodes[0]]))
            total_length = sum(od_matrix[a] for a in zipped_lists)
            if total_length < threshold_max_length:
                dict_all_routes[route_id] = list_of_nodes + [0]
                list_lens_of_routes[route_id] = total_length
                route_id  += 1

    return dict_all_routes, list_lens_of_routes

# a param:
# a =>  1 if a customer lies on  a particular route, 0 otherwise
def create_a_param(dict_all_routes, customers):
    a_i_r = {}
    for i in customers:
        for r in dict_all_routes:
            a_i_r[i,r] = 1 if i in dict_all_routes[r] else 0
    return a_i_r

# e_r:
# e => edges per route as a dictionary, key is route_id


def create_e_r(dict_all_routes):
    edges_per_route = {}
    for k,v in dict_all_routes.items():
        route_id = k
        route_list = v
        zipped_list =  list(zip(route_list, route_list[1:]))
        edges_per_route[route_id ] = zipped_list
    return edges_per_route

# this method returns: a dictionary (of course)
# ... given a customer, and a schedule_id, it returns a dictionary with services as keys and demand per day as value
# if you want to now for example what customer 1 demands according to schedule #1, and want to know about PNC,
# you have to access the dict,  demand_for_cust_sched[1,1]['PNC']
# { 1, 1: {'PNC': 4.0, 'WDS': 6.0}, 1, 2: {'PNC': 7.0, 'WDS': 4.0}}


def find_demand_per_schedule(all_schedules_dict, customer_list, demands_entire_planning_horizont):
    demand_for_cust_sched = {}
    for i in customer_list:
        for s_key, s_val in all_schedules_dict.items():
            number_of_days = len(s_val)
            demand_for_cust_sched[i, s_key] = {k: (lambda l: l / number_of_days)(v) for k, v in demands_entire_planning_horizont[i].items()}
    return demand_for_cust_sched







class Config_Input_PVRP():

    def __init__(self, R, T, P, C_p, a, b, demand, capa, E_r, c, coordinates, S):
        self.R_ids = list(R.keys())
        self.P_ids = list(P.keys())
        self.R = R
        self.T = T
        self.P = P
        self.C_p = C_p
        self.a = a
        self.b = b
        self.demand = demand
        self.capa = capa
        self.E_r = E_r
        self.c = c
        self.coordinates = coordinates
        self.S = S


