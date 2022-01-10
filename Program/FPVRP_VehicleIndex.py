from gurobipy import Model, GRB, quicksum


class FPVRP_VehInd():

    def __init__(self, input_params, next_scenario):
        self.cfg = input_params
        self.mp = Model('P_VRP')

        # scenario dependent data
        self.C = next_scenario.C
        self.num_vecs = next_scenario.num_vecs
        self.scenario = next_scenario

    def __initialize_variables(self):
        self.z = self.mp.addVars(self.C, self.cfg.T, lb=0, vtype=GRB.BINARY)   # if customer i is visited in t or not
        self.y = self.mp.addVars(self.cfg.A, self.cfg.T, vtype=GRB.BINARY)
        self.z_vecs = self.mp.add(self.cfg.T, vtype=GRB.BINARY)
        self.l = self.mp.add(self.cfg.A, self.cfg.T, vtype=GRB.BINARY)
        self.q = self.mp.add(self.cfg.C, self.cfg.T, vtype=GRB.BINARY)

    def __set_default_constraints(self):
        pass

    def set_constraints(self):
        self.__set_default_constraints()


