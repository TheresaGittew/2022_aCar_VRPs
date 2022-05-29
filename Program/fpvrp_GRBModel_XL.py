from gurobipy import Model, GRB, quicksum, tuplelist
from itertools import combinations
from fpvrp_PostProcessing import RouteValidation
import collections
import math

index_hub = 100

# #
# Methods to implement subtour elimination (callback + lazy constraint)
def get_successor(current_arc, traversed_arc_list):
    return [i for i in traversed_arc_list if i[0] == current_arc[0][1]]


def k_d_to_links(selected_y_keys):
    day_vec_to_used_arcs = {}
    for i,j,k,t in selected_y_keys:
        if (k,t) not in day_vec_to_used_arcs:
            new_list = [(i,j)]
            day_vec_to_used_arcs[k,t] = new_list
        else:
            day_vec_to_used_arcs[k,t].append((i,j))
    return day_vec_to_used_arcs

# #
# Aux method which obtains the assigned arcs used by vehicle k on day t and returns
# either "Routes i.O." if all arcs construct a valid route. Otherwise, tuple with k, t, and  list with invalid arcs is
# returned.

def find_shortest_tour_for_d(k_d_to_routelinks):
    min_length = 1
    while min_length < 10:
        for key, traversed_arcs_list in k_d_to_routelinks.items():
            if len(traversed_arcs_list) == min_length and not list(filter(lambda x: x[0] == index_hub, traversed_arcs_list))\
                    and not list(filter(lambda x: x[1] == index_hub, traversed_arcs_list)):
                        k, t = key
                        return (k, t, traversed_arcs_list), '1'
        min_length += 1
    min_length = 2
    while min_length < 10:
        for (k,t), traversed_arcs_list in k_d_to_routelinks.items():
            start_arc = list((filter(lambda x: x[0] == index_hub, traversed_arcs_list)))
            route = []
            next_arc = start_arc
            while len(route) < len(traversed_arcs_list):
                route.append(next_arc)

                # takes first element ("next arc") from returned list from get_successor and
                # then takes second node in tuple as destination
                if next_arc[0][1] == index_hub and len(route) < len(traversed_arcs_list):
                    #
                    return (k, t, traversed_arcs_list), '2'
                next_arc = get_successor(next_arc, traversed_arcs_list)

        min_length += 1
    return 'Routes i.O.'

# #
# main method to identify invalid tours (subtours)
# method starts with shortest routes included in solution and checks validity of tours
# if invalid tours are found, the checking procedure is stopped and all invalid routes of current length are returned

def find_shortest_invalid_tours(k_d_to_routelinks):
    all_routes = sorted(list(k_d_to_routelinks.values()), key= lambda x: len(x))
    all_routes_it = iter(all_routes)

    next_route = next(all_routes_it, None)
    invalid_routes_one_length = []
    found_one_invalid = False
    while next_route:
        validator = RouteValidation(next_route)
        is_valid = validator.get_status()

        if not is_valid:
            found_one_invalid = True
            invalid_routes_one_length.append(next_route)

        old_route = next_route
        next_route = next(all_routes_it, None)

        # #
        # check if next "longer" route has equal length --> further check
        # otherwise finish
        if not next_route:
            return 'Routes i.O.' if not found_one_invalid else invalid_routes_one_length
        elif found_one_invalid and len(next_route) > len(old_route):
            return invalid_routes_one_length



# #
# callback function for gurobipy
def callback(model, where):

    if where == GRB.Callback.MIPSOL:

        vals_y = model.cbGetSolution(model._y)
        z_indices = tuplelist((i,k,t) for i, k, t in model._z.keys())
        max_t =  max([t for (i,k,t) in z_indices])
        max_k = max([k for (i,k,t) in z_indices])

        selected_y_keys = [(i,j,k,t) for i,j,k,t in model._y.keys() if vals_y[i,j,k,t] > 0.5]

        k_d_to_link = k_d_to_links(selected_y_keys)

        shortest_invalid_tours_list = find_shortest_invalid_tours(k_d_to_link)
        if not shortest_invalid_tours_list == 'Routes i.O.':
            for next_invalid_tour in shortest_invalid_tours_list:
                nodes_on_faulty_route = tuple(sorted(list(set([l for sublist in [[i,j] for i,j in next_invalid_tour] for l in sublist]))))
                model._faulty_nodes_so_far.append(nodes_on_faulty_route)

                prepr = FPVRPVecIndPreProcess(nodes_on_faulty_route)
                subset_id_to_A = prepr.get_subset_id_to_A()
                subset_id_to_C = prepr.get_subset_id_to_C()
                C_subset_ids = prepr.get_subset_ids()
                for c_sub_id in C_subset_ids:
                    for i_2 in subset_id_to_C[c_sub_id]:
                        for k in range(max_k+1):
                            for t in range(max_t+1):

                                model.cbLazy(quicksum(model._y[i,j,k,t] for i,j in subset_id_to_A[c_sub_id])
                               <= quicksum(model._z[i,k,t] for i in subset_id_to_C[c_sub_id]) - model._z[i_2, k,t])

            #print("Return from callback \n \n \n")
        else:
            # print("* * * All routes are ok. Finish * * *")
            pass


class VRP_VBS_Optimizer:

    def __init__(self, cfg_params, next_scenario):
        self.cfg = cfg_params
        self.mp = Model('P_VRP')
        self.S = cfg_params.S

        # scenario dependent data
        self.C = next_scenario.C
        self.K = next_scenario.K
        self.N = next_scenario.N
        self.A = next_scenario.A

        self.scenario = next_scenario
        self.__initialize_variables()


    def __initialize_variables(self):
        self.z = self.mp.addVars(self.N, self.K, self.cfg.T, lb=0, vtype=GRB.BINARY, name='z')   # customer visited?
        self.y = self.mp.addVars(self.A, self.K, self.cfg.T, vtype=GRB.BINARY, name='y') # arc usage
        self.z_vecs = self.mp.addVars(self.cfg.T, vtype=GRB.INTEGER, name='z_vecs') # number vecs from node
        self.q = self.mp.addVars(self.C, self.K, self.cfg.T, self.S, vtype=GRB.CONTINUOUS, name='q') # deliveries to users
        self.u = self.mp.addVars(self.cfg.H, self.K, vtype=GRB.BINARY, name='u')


    def set_constraints(self):
        self.__set_default_constraints()
        self.__set_valid_inequalities()
        self.__set_additional_constraints()


    def __set_default_constraints(self):

        # constraint 4.2: no vehicle delivers any customer a quantity that exceeds w_i
        self.mp.addConstrs(self.q[i, k, t, s] <= self.cfg.w[i,s] * self.z[i, k, t] for i in self.C for k in self.K for t in self.cfg.T for s in self.S)

        # constraint 4.3, 4.4 establish that total quantity delivered by k at t does not exceed vehicle capa
        self.mp.addConstrs(quicksum(self.q[i, k, t, s] for i in self.C) <= quicksum(self.cfg.Q_h_s[h][s] * self.u[h,k]  for h in self.cfg.H) for k in self.K for t in self.cfg.T for s in self.S)
        self.mp.addConstrs(quicksum(self.q[i, k, t, s] for i in self.C) <= self.cfg.Q_bigM[s] * self.z[index_hub, k, t]  for k in self.K for t in self.cfg.T for s in self.S)


        # constraint 4.5.: for every vehicle and time period, one arc has to exit from the nod of every visited node
        self.mp.addConstrs(quicksum(self.y[i, j, k, t] for j in self.N if (i,j) in self.A) == self.z[i, k, t]
                           for i in self.N for k in self.K for t in self.cfg.T)

        # constraint 4.6. : flow continuity
        self.mp.addConstrs(quicksum(self.y[i, j, k, t] for j in self.N if (i, j) in self.A) == quicksum(self.y[j, i, k, t] for j in self.N if (j,i) in self.A) for i in self.N for k in self.K for t in self.cfg.T)

        # constraint 4.8: total demand
        self.mp.addConstrs(quicksum(self.q[i, k, t, s] for t in self.cfg.T for k in self.K)
                           >= self.cfg.W[i, s] for i in self.C for s in self.S)

        self.mp.addConstrs(quicksum(self.u[h, k] for h in self.cfg.H)
                           >= self.z[i, k, t] for i in [index_hub] for k in self.K for t in self.cfg.T)

        self.mp.addConstrs(quicksum(self.u[h, k] for h in self.cfg.H)
                           <= 1 for k in self.K)

    def __set_additional_constraints(self):
        print (" .. setting additional constraints ...")
        self.set_max_dist()
        self.set_time_limit()
        self.set_max_num_stops()


    def __set_valid_inequalities(self):
        ##
        print(" .. setting valid inequalities ...")
        ## valid inequalities
        self.set_symmetry_breaking_u()
        self.set_symmetry_breaking_z_1()
        # self.set_symmetry_breaking_z_2()
        # self.set_symmetry_breaking_cx()
        # self.set_ordering_u()
        # self.set_symm_break_lahyani_14()
        # self.set_log_ineq_lahyani_15()
        # self.set_log_ineq_lahyani_17()
        # self.set_log_ineq_lahyani_18()
        # self.set_log_ineq_lahyani_19()
        # self.set_rounded_capacity_cut()

    def set_symmetry_breaking_u(self):
        self.mp.addConstrs(quicksum(self.u[h,k] for h in self.cfg.H ) >= quicksum(self.u[h, k+1] for h in self.cfg.H ) for k in self.K if k != self.K[-1])

    def set_symmetry_breaking_z_1(self): # from Archetti Munoz
        self.mp.addConstrs(self.z[i,k,t]  <= self.z[index_hub, k,t] for i in self.C for k in self.K for t in self.cfg.T)

    def set_symmetry_breaking_z_2(self): # from Archetti Munoz
        self.mp.addConstrs(self.z[index_hub, k, t] >= self.z[index_hub, k+1, t] for k in self.K if k != self.K[-1] for t in self.cfg.T)

    def set_ordering_u(self):
        self.mp.addConstrs(quicksum(self.u[h_1, k-1] for h_1 in self.cfg.H if h_1 <= h) >= self.u[h, k] for h in self.cfg.H for k in self.K if k != 0)

    def set_symm_break_lahyani_14(self):
        self.mp.addConstrs(quicksum(self.u[h_1, k-1] for h_1 in self.cfg.H if h_1 <= h) >= self.u[h, k] for h in self.cfg.H for k in self.K if k != 0)

        self.mp.addConstrs(self.z[i, k,t] <= quicksum(self.z[j, k-1, t]  for j in self.C if j < i)
                           + 7 * (1 - self.u[h, k]) + 7 * (1 - self.u[h, k - 1])
                           for i in self.C for k in self.K if k > 0 for t in self.cfg.T for h in self.cfg.H)

    def set_log_ineq_lahyani_15(self):
        self.mp.addConstrs(self.z[index_hub, k, t] <= quicksum(self.z[i, k, t] for i in self.C) for k in self.K for t in self.cfg.T)

    def set_log_ineq_lahyani_17(self):
        self.mp.addConstrs(self.y[i,j,k,t] <= self.z[j,k,t] for (i,j) in self.A for k in self.K for t in self.cfg.T)

    def set_log_ineq_lahyani_18(self):
        self.mp.addConstrs(quicksum(self.z[i,k,t] for i in self.C) <= quicksum(self.y[i, j, k,t] for (i,j) in self.A) for k in self.K for t in self.cfg.T)

    def set_log_ineq_lahyani_19(self):
        self.mp.addConstrs((self.z[i,k,t]) <=
                           quicksum(self.y[i_2,index_hub,k,t] for i_2 in self.C) for i in self.C for k in self.K for t in self.cfg.T)



    def set_max_num_stops(self):
        print("set max num stops to: ", self.cfg.stop_limit)
        self.mp.addConstrs(quicksum(self.z[i, k, t] for i in self.C ) <= self.cfg.stop_limit for k in self.K for t in self.cfg.T)

    def set_time_limit(self):
        print("set time limit to" , str(self.cfg.time_limit))
        self.mp.addConstrs(quicksum(self.y[i, j, k, t] * self.cfg.travel_time[i,j] for i,j in self.A )
                           + quicksum(self.q[i, k, t, s] * self.cfg.service_time[s] for s in self.cfg.S for i in self.C)

                           <= self.cfg.time_limit for k in self.K for t in self.cfg.T)

    def set_max_dist(self):
        print("set max dist", str(self.cfg.range_limit))
        print("c: ", self.cfg.c)
        self.mp.addConstrs(quicksum(self.y[i, j, k, t] * self.cfg.c[i, j] for i, j in self.A)
                           <= self.cfg.range_limit for k in self.K for t in self.cfg.T)


    def set_objective(self):
        self.mp.modelSense = GRB.MINIMIZE
        self.mp._z = self.z
        self.mp._y = self.y
        self.mp._captured_tours = []
        self.mp._faulty_nodes_so_far = []


        self.mp.setObjective(
            quicksum(self.cfg.f[h] * self.u[h,k] for h in self.cfg.H for k in self.K) +
            quicksum(self.y[i, j, k, t] * self.cfg.c[i, j] * self.cfg.cost_factor_per_km for (i, j)
                     in self.A for t in self.cfg.T for k in self.K))

    def solve_model(self):
        self.mp.Params.MIPGap = 0.25
        self.mp.Params.TimeLimit = 30000 # 12 stunden
        self.mp.Params.LazyConstraints = 1
        self.mp.optimize(callback)

        # #
        # Return value => status of optimization
        if not self.mp.objVal < 1000000:
            return 'NO_GAP'

        if self.mp.status == GRB.OPTIMAL:
            return 'OPTIMAL'

        elif self.mp.status == GRB.INFEASIBLE:
            return 'INFEASIBLE'


    def print_output(self):
        print("RUNTIME ", self.mp.Runtime, " OPTIMAL VALUE " , self.mp.objVal)

# #
# Aux Class required to implement callback function; specifically, to find all subsets of a given set of customer ndoes
# and provide all related links

class FPVRPVecIndPreProcess:

    def __init__(self, C):
        C = [i for i in C if i != index_hub]
        self.C = C
        self.max_length_subset = len(self.C)
        self.__generate_subsets_C()

    def __find_arcs_in_subset(self, subset):
        return [(i,j) for i in subset for j in subset if j != i]

    def __generate_subsets_C(self):

        self.all_subsets_flattened_list = [elem for item in [list(combinations(self.C, length_subset))
                                                        for length_subset in range(2, self.max_length_subset + 1)] for elem in item]

        self.subset_id_to_C = dict((i, self.all_subsets_flattened_list[i]) for i in range(len(self.all_subsets_flattened_list)))
        self.subset_id_to_A = dict((id, self.__find_arcs_in_subset(self.subset_id_to_C[id])) for id in list(self.subset_id_to_C.keys()))

    def get_subset_id_to_C(self):
        return self.subset_id_to_C

    def get_subset_id_to_A(self):
        return self.subset_id_to_A

    def get_subset_ids(self):
        return [i for i  in range(len(self.all_subsets_flattened_list))]


# FPVRPVecIndConfg => class which encapsulates all parameters
class FPVRPVecIndConfg:

    def __init__(self, T,  W_i, w_i, c, coordinates, S, H, travel_time, Q_h_s, fixed_costs_h, service_time,
                 time_limit, stop_limit, range_limit, cost_factor_per_km):

        self.T = T
        self.W = W_i # total demand for entire planning horizon (nested dict)
        self.w = w_i # daily demand (nested dict)
        # self.Q = capa

        self.c = c
        self.coordinates = coordinates
        self.S = S
        self.travel_time = travel_time

        self.service_time = service_time
        #print("self service time ", self.service_time)
        self.time_limit = time_limit
        self.stop_limit = stop_limit
        self.range_limit = range_limit
        self.cost_factor_per_km = cost_factor_per_km


        self.H = H
        self.Q_h_s = Q_h_s
        self.Q_bigM = dict((s, max(self.Q_h_s[h][s] for h in self.H)) for s in self.S)
        self.f = fixed_costs_h






