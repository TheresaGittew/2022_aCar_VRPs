from gurobipy import Model, GRB, quicksum, tuplelist
from itertools import combinations


def get_successor(current_arc, traversed_arc_list):
   #  print("current acr " , current_arc[0])
    #print(" traversed arcs : ", traversed_arc_list)
    returned = [i for i in traversed_arc_list if i[0] == current_arc[0][1]]
    #print (returned)
    return returned

def subtour_dict(selected_y_keys):
    day_vec_to_used_arcs = {}
    for i,j,k,t in selected_y_keys:
        if (k,t) not in day_vec_to_used_arcs:
            new_list = [(i,j)]
            day_vec_to_used_arcs[k,t] = new_list
        else:
            day_vec_to_used_arcs[k,t].append((i,j))
    return day_vec_to_used_arcs

def find_shortest_subtour_without_hub(subtour_dict):
    min_length = 1

    # step 1 : remove tours that don#t go back to node
    while min_length < 10:

        for key, traversed_arcs_list in subtour_dict.items():
            if len(traversed_arcs_list) == min_length and not list(filter(lambda x: x[0] == 0, traversed_arcs_list))\
                    and not list(filter(lambda x: x[1] == 0, traversed_arcs_list)):
                        print(" are in first part with ", traversed_arcs_list)
                        k, t = key
                        return (k, t, traversed_arcs_list)

        min_length += 1

    min_length = 2
    while min_length < 10:
        for key, traversed_arcs_list in subtour_dict.items():
            k, t = key
            start_arc = list((filter(lambda x: x[0] == 0, traversed_arcs_list)))
            route = []
            next_arc = start_arc
            print(traversed_arcs_list)
            while len(route) < len(traversed_arcs_list):
                route.append(next_arc)
                if next_arc[0][1] == 0 and len(route) < len(traversed_arcs_list):  # takes first element ("next arc") from returned list from get_successor and then takes second node in tuple as destination
                    print(next_arc)
                    print("are in second part with this list here ", traversed_arcs_list)
                    return (k, t, traversed_arcs_list)
                next_arc = get_successor(next_arc, traversed_arcs_list)

        min_length += 1
    return 'Routes i.O.'



def mycallback(model, where):
    #print("are in callback")
    if where == GRB.Callback.MIPSOL:
        print("+ + + +\n next call mycallbaack + + + +")

        # get z
        vals_z = model.cbGetSolution(model._z) # z has dimension i, k, t
        vals_y = model.cbGetSolution(model._y)
        selected_z = tuplelist((i,k,t) for i, k, t in model._z.keys() if vals_z[i,k,t] > 0.5)
        max_t =  max([t for (i,k,t) in selected_z])
        max_k = max([k for (i,k,t) in selected_z])
        print("max t: " , max_t, " max_k : ", max_k)


        selected_y = tuplelist(() for i,j,k,t in model._y.keys() if vals_y[i,j,k,t] > 0.5)
        selected_y_keys = [(i,j,k,t) for i,j,k,t in model._y.keys() if vals_y[i,j,k,t] > 0.5]

        day_vec_to_used_arcs = subtour_dict(selected_y_keys)
        print("day_veec_to_used_arcs", day_vec_to_used_arcs)
        results_subtour_check = find_shortest_subtour_without_hub(day_vec_to_used_arcs)

        if not results_subtour_check == 'Routes i.O.':
            print("* * * mycallback has been called. One faulty route has been found. Finish * * *")
            k, t, arcs_on_faulty_route = results_subtour_check[0], results_subtour_check[1], results_subtour_check[2]
            nodes_on_faulty_route = list(set([l for sublist in [[i,j] for i,j in arcs_on_faulty_route] for l in sublist]))
            print("Nodes on faulty route: ", nodes_on_faulty_route)

            # get subsets
            prepr = FPVRPVecIndPreProcess(nodes_on_faulty_route, arcs_on_faulty_route)
            subset_id_to_A = prepr.get_subset_id_to_A()
            subset_id_to_C = prepr.get_subset_id_to_C()
            C_subset_ids = prepr.get_subset_ids()
            print("Customers for new constraint: ", subset_id_to_C)


            for c_sub_id in C_subset_ids:
                for i_2 in subset_id_to_C[c_sub_id]:
                    for k in range(max_k+1):
                        for t in range(max_t+1):
                                model.cbLazy(quicksum(model._y[i,j,k,t] for i,j in subset_id_to_A[c_sub_id])
                               <= quicksum(model._z[i,k,t] for i in subset_id_to_C[c_sub_id]) - model._z[i_2, k,t])
        else:
            print("* * * mycallback has been called. All routes are ok. Finish * * *")


class FPVRPSVehInd:

    def __init__(self, input_params, next_scenario):
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

    def __initialize_variables(self):
        self.z = self.mp.addVars(self.N, self.K, self.cfg.T, lb=0, vtype=GRB.BINARY, name='z')   # customer visited?
        self.y = self.mp.addVars(self.cfg.A, self.K, self.cfg.T, vtype=GRB.BINARY, name='y') # arc usage
        self.z_vecs = self.mp.addVars(self.cfg.T, vtype=GRB.INTEGER, name='z_vecs') # number vecs from node
        self.q = self.mp.addVars(self.C, self.K, self.cfg.T, self.S, vtype=GRB.CONTINUOUS, name='q') # deliveries to users

    def __set_default_constraints(self):
        print(" .. setting default constraint 4.2 ... ")

        # constraint 4.2: no vehicle delivers any customer a quantity that exceeds w_i
        self.mp.addConstrs(self.q[i, k, t, s] <= self.cfg.w[i,s] * self.z[i, k, t] for i in self.C for k in self.K for t in self.cfg.T for s in self.S)
        print(" .. setting default constraint 4.3  ... ")
        # constraint 4.3: establish that total quantity delivered by k at t does not exceed vehicle capa
        self.mp.addConstrs(quicksum(self.q[i, k, t, s] for i in self.C) <= self.cfg.Q[k, s] * self.z[100, k, t] for k in self.K for t in self.cfg.T for s in self.S)
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

        # aux constraint
        # self.mp.addConstrs(quicksum(self.y[i, j, k, t] for (i,j)  in self.cfg.A) >= 3
        #                     for k in self.K for t in
        #                    self.cfg.T)
        #print(" .. setting default constraint 4.8  ... ")

        # constraint 4.7
        #self.set_subtour_elim_constraint() # bärstig
        pass

    def set_subtour_elim_constraint(self):
        print(" .. setting default constraint 4.7  ... ")
        subtour_elim_constrs = self.mp.addConstrs(quicksum(self.y[i,j,k,t] for i,j in self.cfg.subset_id_to_A[c_sub_id])
                          <= quicksum(self.z[i,k,t] for i in self.cfg.subset_id_to_C[c_sub_id]) - self.z[i_2, k,t]
                          for c_sub_id in self.cfg.C_subset_ids for i_2 in self.cfg.subset_id_to_C[c_sub_id]
                          for k in self.K for t in self.cfg.T)

        # for t in self.cfg.T:
        #     for k in self.K:
        #         for c_sub_id in self.cfg.C_subset_ids:
        #             for i_2 in self.cfg.subset_id_to_C[c_sub_id]:
        #                 subtour_elim_constrs[c_sub_id, i_2, k, t].Lazy = 2
        # print(" ... finished setting constraints .. ")

    def set_constraints(self):
        self.__set_default_constraints()



    def set_objective(self):
        self.mp.modelSense = GRB.MINIMIZE

        print(" .. set objective ...")
        self.mp._z = self.z
        self.mp._y = self.y

        # here, you can potentially add further cost factors
        self.mp.setObjective(
            quicksum(self.y[i, j, k, t] * self.cfg.c[i, j] for (i, j) in self.cfg.A for t in self.cfg.T for k in self.K))

    def solve_model(self):
        self.mp.Params.MIPGap = 0.001  # self.mp.Params.TimeLimit = 5000
        self.mp.Params.LazyConstraints = 1
        self.mp.optimize(mycallback)
        self.print_output()





    def print_output(self):

        for v in self.mp.getVars():
            if v.x > 0:
                print("Variable: " , v, " Value: " , v.X)

        print("Optimal Value : " , self.mp.objVal)

class FPVRPVecIndPreProcess:

    def __init__(self, C, A):
        print("these are the customers on faulty route: ", C)
        self.C = C
        self.A = A
        #print("these are the given arcs : " , A )
        self.num_custs = len(C)
        self.__generate_subsets_C()

    def __generate_subsets_C(self):

        self.all_subsets_flattened_list = [elem for item in [list(combinations(self.C, length_subset))
                                                        for length_subset in range(2, self.num_custs)] for elem in item]

        self.subset_id_to_C = dict((i, self.all_subsets_flattened_list[i]) for i in range(len(self.all_subsets_flattened_list)))
        #print(self.subset_id_to_C)
        self.subset_id_to_A = dict((self.all_subsets_flattened_list.index(subset), (lambda x: list(filter(lambda a: a[0] in subset and a[1] in subset, self.A.copy())))(subset))
                                   for subset in self.all_subsets_flattened_list)


    def get_subset_id_to_C(self):
        return self.subset_id_to_C

    def get_subset_id_to_A(self):
        return self.subset_id_to_A

    def get_subset_ids(self):
        return [i for i  in range(len(self.all_subsets_flattened_list))]


class FPVRPVecIndConfg:

    def __init__(self, T, A, W_i, w_i, capa, c, coordinates, S):

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

        # self.C_subset_ids = subset_ids
        # self.subset_id_to_C = subset_id_to_C
        # self.subset_id_to_A = subset_id_to_A





