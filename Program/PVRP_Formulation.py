from gurobipy import Model, GRB, quicksum


class PVRP_Formulation():

    # scenarios as a tuple with combination of # vehicles, relevant customers
    def __init__(self, input_params, next_scenario):
        self.cfg = input_params
        self.mp = Model('P_VRP')

        # scenario dependent data
        self.C = next_scenario.C
        self.num_vecs = next_scenario.num_vecs
        self.scenario = next_scenario

        # set up variables
        self.__initialize_variables()



    def __initialize_variables(self):
        self.x = self.mp.addVars(self.cfg.R_ids, self.cfg.T, lb=0, vtype=GRB.BINARY)  # equal to 1 if route r is performed on day t
        self.y = self.mp.addVars( self.C, self.cfg.P_ids, lb=0, vtype=GRB.BINARY)  # y_i_p equal to 1 if schedule p is selected for customer i
        #self.z = self.mp.addVars(self.cfg.R_ids, self.C, self.cfg.T, lb=0, vtype=GRB.BINARY) # z_r_c_t is 1 if a route is selected for day t and customer c lies on that route, 0 otherwise
        self.demand_t = self.mp.addVars(self.cfg.T, self.C, lb=0, vtype=GRB.CONTINUOUS)

    def set_constraints(self):
        self.__set_default_constraints()

        # add further method calls in case u want to have additional constraints (e.g. battery capacity

    def __set_default_constraints(self):
        self.mp.addConstrs(quicksum(self.y[i,p] for p in self.cfg.C_p[i]) == 1 for i in self.C)

        self.mp.addConstrs(quicksum(self.x[r, t] * self.cfg.a[i, r] for r in self.cfg.R_ids)
                           - quicksum(self.y[i, p] * self.cfg.b[p, t] for p in self.cfg.C_p[i]) >= 0 for i in self.C for t in self.cfg.T)

        # setup z
        # self.mp.addConstrs(self.z[r, i, t] >= self.y[i, p] * self.cfg.b[p, t] * self.cfg.a[i,r] + (self.x[r,t] - 1) for i in self.C for p in self.cfg.P_ids for r in self.cfg.R_ids for t in self.cfg.T)
        # self.mp.addConstrs(self.z[r, i, t] <= self.x[r,t] for i in self.C  for r in self.cfg.R_ids for t in self.cfg.T)
        # self.mp.addConstrs(self.z[r, i, t] <= self.y[i, p] for i in self.C for r in self.cfg.R_ids  for p in self.cfg.P_ids for t in self.cfg.P[p])
        for t in self.cfg.T:
            for p in self.cfg.P_ids:
                for i in self.C:
                    self.mp.addConstr(self.cfg.demand[i, p]['PNC'] * self.y[i, p] * self.cfg.b[p, t] <= self.demand_t[t, i])


        for r in self.cfg.R_ids:
            for t in self.cfg.T:
                self.mp.addConstr(quicksum(self.demand_t[t, i] * self.cfg.a[i,r] for i in self.C) <= self.cfg.capa + ((1 - self.x[r,t]) * 100))

      #  self.mp.addConstrs(quicksum(quicksum(self.cfg.demand[i, p]['PNC'] for p in self.cfg.C_p[i]) for i in self.C) <= self.cfg.capa for t in self.cfg.T for r in self.cfg.R_ids)

        self.mp.addConstrs(quicksum(self.x[r, t] for r in self.cfg.R_ids) <= self.num_vecs for t in self.cfg.T) # respect number of available vehicles

    def set_objective(self):
        print(" ... Are in set objective ... ")
        self.mp.modelSense = GRB.MINIMIZE

        # here, you can potentially add further cost factors
        #print(self.cfg.c)
        self.mp.setObjective(
            sum(sum(sum(self.x[r, t] * self.cfg.c[i, j] for (i, j) in self.cfg.E_r[r]) for r in self.cfg.R_ids) for t in self.cfg.T))

    def solve_model(self):
        self.mp.Params.MIPGap = 0.001  # self.mp.Params.TimeLimit = 5000
        # self.mp.setParam('OutputFlag', 0)
        self.mp.optimize()
        self.get_output()

    def get_output(self):


        return self


