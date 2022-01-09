from gurobipy import Model, GRB, quicksum


class PVRPS_Formulation():

    def __init__(self, input_params, next_scenario):
        self.cfg = input_params
        self.mp = Model('P_VRP')

        # scenario dependent data
        self.C = next_scenario.C
        self.num_vecs = next_scenario.num_vecs
        self.V = [v for v in range(self.num_vecs)]
        self.scenario = next_scenario

        # set up variables
        self.__initialize_variables()

    def __initialize_variables(self):
        self.x = self.mp.addVars(self.cfg.R_ids, self.cfg.T, self.cfg.S, lb=0, vtype=GRB.BINARY)  # equal to 1 if route r is performed on day t
        self.y = self.mp.addVars( self.C, self.cfg.P_ids, self.cfg.S, lb=0, vtype=GRB.BINARY)  # y_i_p equal to 1 if schedule p is selected for customer i
        self.demand_t = self.mp.addVars(self.cfg.T, self.C, self.cfg.S, lb=0, vtype=GRB.CONTINUOUS)
        self.h = self.mp.addVars(self.V, self.cfg.R_ids, self.cfg.T, lb = 0, vtype=GRB.BINARY)

    def set_constraints(self):
        self.__set_default_constraints()

    def __set_default_constraints(self):

        ##
        # constraint 1
        self.mp.addConstrs(quicksum(self.y[i,p, s] for p in self.cfg.C_p[i, s]) == 1 for s in self.cfg.S for i in self.C)

        ##
        # constraint 2
        self.mp.addConstrs(quicksum(self.x[r, t, s] * self.cfg.a[i, r] for r in self.cfg.R_ids)
                           - quicksum(self.y[i, p, s] * self.cfg.b[p, t] for p in self.cfg.C_p[i, s]) >= 0 for s in self.cfg.S
                           for i in self.C for t in self.cfg.T)

        # constraint 3
        for t in self.cfg.T:
            for p in self.cfg.P_ids:
                for s in self.cfg.S:
                    for i in self.C:
                        self.mp.addConstr(self.cfg.demand[i, p][s] * self.y[i, p, s] * self.cfg.b[p, t] <= self.demand_t[t, i, s])

        # constraint 4
        for r in self.cfg.R_ids:
            for t in self.cfg.T:
                for s in self.cfg.S:
                    self.mp.addConstr(quicksum(self.demand_t[t, i, s] * self.cfg.a[i,r] for i in self.C) <= quicksum( self.cfg.capa[v,s] * self.h[v,r,t] for v in self.V) + ((1 - self.x[r,t, s]) * 100))

        ##
        # constraint 5 : vehicle number should be respected
        self.mp.addConstrs(quicksum(quicksum(self.h[v, r, t] for v in self.V) for r in self.cfg.R_ids) <= self.num_vecs for t in self.cfg.T)

        ##
        # constraint 5b: only one vehicle per route and per day
        self.mp.addConstrs(quicksum(self.h[v, r, t] for r in self.cfg.R_ids) <= 1 for t in self.cfg.T for v in self.V)

        ##
        # constraint 6 : new, connect h and x
        self.mp.addConstrs(self.x[r, t, s] <= quicksum(self.h[v, r, t] * self.cfg.capa[v, s] for v in self.V) for t in self.cfg.T for s in self.cfg.S for r in self.cfg.R_ids)

    def set_objective(self):
        self.mp.modelSense = GRB.MINIMIZE

        # here, you can potentially add further cost factors
        #print(self.cfg.c)
        self.mp.setObjective(
            sum(sum(sum(sum(self.x[r, t, s] * self.cfg.c[i, j] for (i, j) in self.cfg.E_r[r]) for r in self.cfg.R_ids) for t in self.cfg.T) for s in self.cfg.S)
            + sum(sum(sum(self.h[v,r,t]  for r in self.cfg.R_ids) for t in self.cfg.T) for v in self.V)


        )

    def solve_model(self):
        self.mp.Params.MIPGap = 0.001  # self.mp.Params.TimeLimit = 5000
        # self.mp.setParam('OutputFlag', 0)
        self.mp.optimize()
        self.get_output()

    def get_output(self):
        print("This is the demand")
        for k,v in self.demand_t.items():
            if v.X >= 0.6:
                print("Key: ", k, " value: ", v.X)

        return self


