from gurobipy import Model, GRB, quicksum, tuplelist
from itertools import combinations
from fpvrp_PostProcessing import RouteValidation
import collections

index_hub = 100

def get_successor(current_arc, traversed_arc_list):
   #  print("current acr " , current_arc[0])
    #print(" traversed arcs : ", traversed_arc_list)
    returned = [i for i in traversed_arc_list if i[0] == current_arc[0][1]]
    #print (returned)
    return returned

def k_d_to_links(selected_y_keys):
    day_vec_to_used_arcs = {}
    for i,j,k,t in selected_y_keys:
        if (k,t) not in day_vec_to_used_arcs:
            new_list = [(i,j)]
            day_vec_to_used_arcs[k,t] = new_list
        else:
            day_vec_to_used_arcs[k,t].append((i,j))
    return day_vec_to_used_arcs

# rename subtour dict to used-arcs
def find_shortest_tour_for_d(k_d_to_routelinks):
    min_length = 1

    # step 1 :this part should actually be irrelevant as all tours include one arc where o = index_hub and
    # one where d = index_hub
    while min_length < 10:
        for key, traversed_arcs_list in k_d_to_routelinks.items():
            if len(traversed_arcs_list) == min_length and not list(filter(lambda x: x[0] == index_hub, traversed_arcs_list))\
                    and not list(filter(lambda x: x[1] == index_hub, traversed_arcs_list)):
                        print(" are in first part with ", traversed_arcs_list)
                        k, t = key
                        return (k, t, traversed_arcs_list), '1'

        min_length += 1

    min_length = 2
    # #
    # todo: aktuelle Heuristik ist ja so: es wird das erstbeste routelinks gewählt, das nicht valide ist.
    # das könnte man noch abändern, sodass z.b. die kürzeste route gewählt wird. (d.h. länge traversed arc list sortieren)
    while min_length < 10:
        for (k,t), traversed_arcs_list in k_d_to_routelinks.items():
            # print("are in min length 2 with the following subtour : ", subtour_dict)

            start_arc = list((filter(lambda x: x[0] == index_hub, traversed_arcs_list)))
            route = []
            next_arc = start_arc
            # print(traversed_arcs_list)
            while len(route) < len(traversed_arcs_list):
                route.append(next_arc)
                if next_arc[0][1] == index_hub and len(route) < len(traversed_arcs_list):  # takes first element ("next arc") from returned list from get_successor and then takes second node in tuple as destination
                    print(next_arc)
                    # print("are in second part with this list here ", traversed_arcs_list)
                    return (k, t, traversed_arcs_list), '2'
                next_arc = get_successor(next_arc, traversed_arcs_list)

        min_length += 1
    print("are here")
    return 'Routes i.O.'


# # todo wichtige annahme bei der methodik hier: wir fangen mit kürzesten routen an, und eliminieren sie aber für
# # todo alle Zeitfenster und alle Fahrzeuge!

def find_shortest_invalid_tours(k_d_to_routelinks):
    all_routes = sorted(list(k_d_to_routelinks.values()), key= lambda x: len(x))
    all_routes_it = iter(all_routes)

    next_route = next(all_routes_it, None)
    invalid_routes_one_length = []
    found_one_invalid = False
    while next_route:
        validator = RouteValidation(next_route)
        is_valid = validator.get_status()
        print("Check next route :", next_route, " is valid ? ", is_valid)

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
        elif found_one_invalid and len(next_route) > len(old_route): # there is a next route but the next route is longer than current one
            return invalid_routes_one_length





def mycallback(model, where):

    if where == GRB.Callback.MIPSOL:
        print("\n\n+ + + + next call of callback function + + + +")

        # get z
        vals_z = model.cbGetSolution(model._z) # z has dimension i, k, t
        vals_y = model.cbGetSolution(model._y)
        selected_z = tuplelist((i,k,t) for i, k, t in model._z.keys() if vals_z[i,k,t] > 0.5)
        max_t =  max([t for (i,k,t) in selected_z])
        max_k = max([k for (i,k,t) in selected_z])
        # print("max t: " , max_t, " max_k : ", max_k)


        selected_y = tuplelist(() for i,j,k,t in model._y.keys() if vals_y[i,j,k,t] > 0.5)
        selected_y_keys = [(i,j,k,t) for i,j,k,t in model._y.keys() if vals_y[i,j,k,t] > 0.5]

        k_d_to_link = k_d_to_links(selected_y_keys)

        # print("These are the selected k_d_to_links" , k_d_to_link)
        shortest_invalid_tours_list = find_shortest_invalid_tours(k_d_to_link)
        #model._captured_tours.append(shortest_invalid_tours_list)
        if not shortest_invalid_tours_list == 'Routes i.O.':
            # print ("shortest invalid tour list" , shortest_invalid_tours_list)
            for next_invalid_tour in shortest_invalid_tours_list:
                #print("Next faulty route: ", next_invalid_tour)
                #print("* * * mycallback has been called. One faulty route has been found. Finish * * *")

                nodes_on_faulty_route = tuple(sorted(list(set([l for sublist in [[i,j] for i,j in next_invalid_tour] for l in sublist]))))
                if nodes_on_faulty_route in model._faulty_nodes_so_far:
                    print("CHECK || ", nodes_on_faulty_route, " has already been captured before ! ")
                # print("Nodes on faulty route sorted : " , nodes_on_faulty_route)
                model._faulty_nodes_so_far.append(nodes_on_faulty_route)
                duplicates = [item for item, count in collections.Counter(model._faulty_nodes_so_far).items() if count > 1]
                #print("Duplicates ? ", duplicates)
                #print("Nodes on faulty route: ", nodes_on_faulty_route)

                # get subsets

                # if error_code == '1':
                #     pass
                    # print("Error code 1")
                    # for i in nodes_on_faulty_route:
                    #     for k in range(max_k + 1):
                    #         for t in range(max_t + 1):
                    #             model.cbLazy(model._z[i,k,t] <= model._z[index_hub, k, t])

                prepr = FPVRPVecIndPreProcess(nodes_on_faulty_route)
                subset_id_to_A = prepr.get_subset_id_to_A()
                subset_id_to_C = prepr.get_subset_id_to_C()
                C_subset_ids = prepr.get_subset_ids()
                for c_sub_id in C_subset_ids:
                    for i_2 in subset_id_to_C[c_sub_id]:
                        for k in range(max_k+1):
                            for t in range(max_t+1):
                               # print("- - - we add a new lazy constraint for set", subset_id_to_C[c_sub_id], " - - ", " s: ", i_2, ", k: ", k, ", t: ", t)
                                model.cbLazy(quicksum(model._y[i,j,k,t] for i,j in subset_id_to_A[c_sub_id])
                               <= quicksum(model._z[i,k,t] for i in subset_id_to_C[c_sub_id]) - model._z[i_2, k,t])

            # print("This is current list with so far identified route sets", model._faulty_nodes_so_far)
            print(" We now leave the callback \n \n \n")
        else:
            print("* * * mycallback has been called. All routes are ok. Finish * * *")


def funct_weight_to_range(load_weight_total, max_weight=1000, max_range=300, min_range=50):
    return max_range - ((max_range - min_range) / max_weight) * load_weight_total


print(funct_weight_to_range(65+(13*0.3)))

class FPVRPSVehInd:

    def __init__(self, input_params, next_scenario, with_battery=False):
        self.cfg = input_params
        self.mp = Model('P_VRP')
        self.S = input_params.S

        # scenario dependent data
        self.C = next_scenario.C
        self.K = next_scenario.K
        self.N = next_scenario.N
        print("self.N in fpvrp: " , self.N)

        self.scenario = next_scenario
        self.__initialize_variables()

        self.with_battery = with_battery
        if with_battery:
            self.__initialize_variables_batt_constr()

    def __initialize_variables(self):
        self.z = self.mp.addVars(self.N, self.K, self.cfg.T, lb=0, vtype=GRB.BINARY, name='z')   # customer visited?
        self.y = self.mp.addVars(self.cfg.A, self.K, self.cfg.T, vtype=GRB.BINARY, name='y') # arc usage
        self.z_vecs = self.mp.addVars(self.cfg.T, vtype=GRB.INTEGER, name='z_vecs') # number vecs from node
        self.q = self.mp.addVars(self.C, self.K, self.cfg.T, self.S, vtype=GRB.CONTINUOUS, name='q') # deliveries to users


    def __initialize_variables_batt_constr(self):
        self.l = self.mp.addVars(self.N, self.N, self.K, self.cfg.T, self.S, vtype=GRB.CONTINUOUS,name='l', lb=0)
        self.battery = self.mp.addVars(self.N, self.K, self.cfg.T, vtype=GRB.CONTINUOUS,name='battery', ub=1, lb=0)
        self.full_rng_for_l = self.mp.addVars(self.N, self.K, self.cfg.T, vtype=GRB.CONTINUOUS,name='full_range')


    def __set_default_constraints(self):
        print(" .. setting default constraint 4.2 ... ")

        # constraint 4.2: no vehicle delivers any customer a quantity that exceeds w_i
        self.mp.addConstrs(self.q[i, k, t, s] <= self.cfg.w[i,s] * self.z[i, k, t] for i in self.C for k in self.K for t in self.cfg.T for s in self.S)
        print(" .. setting default constraint 4.3  ... ")
        # constraint 4.3: establish that total quantity delivered by k at t does not exceed vehicle capa
        self.mp.addConstrs(quicksum(self.q[i, k, t, s] for i in self.C) <= self.cfg.Q[k, s] * self.z[index_hub, k, t] for k in self.K for t in self.cfg.T for s in self.S)
        print(" .. setting default constraint 4.4  ... ")
        # constraint 4.4.: at each time period, at most 1 vehicle serves the demand of customer i
        self.mp.addConstrs(quicksum(self.z[i, k, t] for k in self.K) <= 1 for i in self.C for t in self.cfg.T)
        print(" .. setting default constraint 4.5  ... ")
        # constraint 4.5.: for every vehicle and time period, one arc has to exit from the nod of every visited node
        self.mp.addConstrs(quicksum(self.y[i, j, k, t] for j in self.N if (i,j) in self.cfg.A) == self.z[i, k, t]
                           for i in self.N for k in self.K for t in self.cfg.T)

        print(" .. setting default constraint 4.6  ... ")
        # constraint 4.6. : flow continuity
        self.mp.addConstrs(quicksum(self.y[i, j, k, t] for j in self.N if (i, j) in self.cfg.A) == quicksum(self.y[j, i, k, t] for j in self.N if (j,i) in self.cfg.A) for i in self.N for k in self.K for t in self.cfg.T)
        print(" .. setting default constraint 4.8 . ... ")
        # constraint 4.8: total demand
        self.mp.addConstrs(quicksum(self.q[i, k, t, s] for t in self.cfg.T for k in self.K)
                           >= self.cfg.W[i, s] for i in self.C for s in self.S)

        self.set_max_num_stops()

    def set_max_num_stops(self): # todo => max_stops in config class
        self.mp.addConstrs(quicksum(self.z[i, k, t] for i in self.C ) <= self.cfg.stop_limit for k in self.K for t in self.cfg.T)

    def set_time_limit(self):
        print("travel times: ", self.cfg.travel_time)
        self.mp.addConstrs(quicksum(self.y[i, j, k, t] * self.cfg.travel_time[i,j] for i,j in self.cfg.A )
                           + quicksum(self.q[i, k, t, s] * self.cfg.service_time[s] for s in self.cfg.S for i in self.C)

                           <= self.cfg.time_limit for k in self.K for t in self.cfg.T)

    def set_max_dist(self):  # todo => times & limit in config class
        print("travel times: ", self.cfg.travel_time)
        self.mp.addConstrs(quicksum(self.y[i, j, k, t] * self.cfg.c[i, j] for i, j in self.cfg.A)
                           <= self.cfg.range_limit for k in self.K for t in self.cfg.T)


    def set_battery_constraints(self):
        print("... setting battery constraints ... ")
        self.mp.addConstrs(quicksum(self.l[i, j, k, t, s] for i in self.N if (i,j) in self.cfg.A)
                           == quicksum(self.l[j, i_2, k, t, s] for i_2 in self.N if (j, i_2) in self.cfg.A) + self.q[j, k, t, s]
                          for j in self.C for k in self.K for t in self.cfg.T for s in self.S)

        self.mp.addConstrs(self.l[i, index_hub, k, t, s]  == 0
                           for i in self.N if (i, index_hub) in self.cfg.A for k in self.K for t in self.cfg.T for s in self.S)


        self.mp.addConstrs(
            self.l[i, j, k, t, s] <= (self.y[i, j, k, t]) * 1500
            for i in self.N for j in self.C if (i, j) in self.cfg.A for k in self.K for t in self.cfg.T for s in self.S)

        for t in self.cfg.T:
            for k in self.K:
                for i in self.N:
                    for j in self.N:
                        if (i,j) in self.cfg.A:

                            if i == index_hub:
                                self.mp.addConstr(
                                    self.full_rng_for_l[i, k, t] - self.cfg.c[i, j] >=
                                    self.battery[j, k, t] * self.full_rng_for_l[i, k, t] - 5000 * (
                                            1 - self.y[i, j, k, t]))
                            elif j == index_hub:
                                self.mp.addConstr(self.battery[i, k, t] * self.full_rng_for_l[i, k, t] - self.cfg.c[i, j] >=
                                    - 5000 * (1 - self.y[i, j, k, t]))
                            else:
                                self.mp.addConstr(self.battery[i, k, t] * self.full_rng_for_l[i, k, t] -  self.cfg.c[i, j] >=
                                                  self.battery[j, k, t] * self.full_rng_for_l[i, k, t] - 5000 * (1 - self.y[i, j, k, t]))



        weights = {'PNC': 0.3, 'WDS' : 1}
        for t in self.cfg.T:
            for k in self.K:
                for i in self.N:
                    self.mp.addConstr(self.full_rng_for_l[i, k, t] ==
                                                  funct_weight_to_range(quicksum(self.l[i, j, k, t, s] * weights[s]
                                                                                 for s in self.cfg.S for j in self.C if (i,j) in self.cfg.A)))
                # todo: not n?!
        #self.mp.addConstrs( self.battery[i, k, t] >= 0 for i in [index_hub] for k in self.K for t in self.cfg.T)



    def set_subtour_elim_constraint(self):
        print(" .. setting default constraint 4.7  ... ")
        subtour_elim_constrs = self.mp.addConstrs(quicksum(self.y[i,j,k,t] for i,j in self.cfg.subset_id_to_A[c_sub_id])
                          <= quicksum(self.z[i,k,t] for i in self.cfg.subset_id_to_C[c_sub_id]) - self.z[i_2, k,t]
                          for c_sub_id in self.cfg.C_subset_ids for i_2 in self.cfg.subset_id_to_C[c_sub_id]
                          for k in self.K for t in self.cfg.T)


    def set_constraints(self):
        self.__set_default_constraints()

        if self.with_battery:
            self.set_battery_constraints()



    def set_objective(self):
        self.mp.modelSense = GRB.MINIMIZE

        print(" .. set objective ...")
        self.mp._z = self.z
        self.mp._y = self.y
        self.mp._captured_tours = []
        self.mp._faulty_nodes_so_far = []

        # here, you can potentially add further cost factors
        self.mp.setObjective(
            quicksum(self.y[i, j, k, t] * self.cfg.c[i, j] for (i, j) in self.cfg.A for t in self.cfg.T for k in self.K))

    def solve_model(self):
        self.mp.Params.MIPGap = 0.001  # self.mp.Params.TimeLimit = 5000
        self.mp.Params.LazyConstraints = 1
        self.mp.Params.NonConvex = 2
        self.mp.optimize(mycallback)
        self.print_output()





    def print_output(self):

        for v in self.mp.getVars():
            if v.x > 0:
                print("Variable: " , v, " Value: " , v.X)

        print("Optimal Value : " , self.mp.objVal)
        print(" + + + ")
        print("Captured nodes per tour : ", [i for item in self.mp._captured_tours for i in item] )

class FPVRPVecIndPreProcess:

    def __init__(self, C):
        # remove 100 (hub index)
        C = [i for i in C if i != index_hub]


        print("these are the customers on faulty route: ", C)
        self.C = C
        # print("these are the given arcs : " , A )
        self.max_length_subset = len(self.C)
        # self.A = A
        self.__generate_subsets_C()

    def __find_arcs_in_subset(self, subset):
        return [(i,j) for i in subset for j in subset if j != i]

    def __generate_subsets_C(self):

        self.all_subsets_flattened_list = [elem for item in [list(combinations(self.C, length_subset))
                                                        for length_subset in range(2, self.max_length_subset + 1)] for elem in item]

        self.subset_id_to_C = dict((i, self.all_subsets_flattened_list[i]) for i in range(len(self.all_subsets_flattened_list)))
        #print("generated customers per subset: ", self.subset_id_to_C) # for a given set of customers, find all possible subsets for subtour elim constraints
        # todo ceheck if this works as intended
        self.subset_id_to_A = dict((id, self.__find_arcs_in_subset(self.subset_id_to_C[id])) for id in list(self.subset_id_to_C.keys()))
        #print("generated arcs per subset ", self.subset_id_to_A) # all possible arc combinations for the given subset

    def get_subset_id_to_C(self):
        return self.subset_id_to_C

    def get_subset_id_to_A(self):
        return self.subset_id_to_A

    def get_subset_ids(self):
        return [i for i  in range(len(self.all_subsets_flattened_list))]


class FPVRPVecIndConfg:

    def __init__(self, T, A, W_i, w_i, capa, c, coordinates, S, travel_time, service_time={'WDS':0.0001, 'PNC':0.25}, time_limit=7, stop_limit=4, range_limit=200):

        self.T = T
        self.A = A
        print(self.A)
        self.W = W_i # total demand for entire planning horizon (nested dict)
        self.w = w_i # daily demand (nested dict)
        print(self.w)
        self.Q = capa

        self.c = c
        self.coordinates = coordinates
        self.S = S
        self.travel_time = travel_time

        self.service_time = service_time
        self.time_limit = time_limit
        self.stop_limit = stop_limit
        self.range_limit = range_limit

        # self.C_subset_ids = subset_ids
        # self.subset_id_to_C = subset_id_to_C
        # self.subset_id_to_A = subset_id_to_A





