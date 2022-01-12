class Scenario():

    def __init__(self, number_vehicles, lower_bound, upper_bound, relevant_customers, T):
        self.num_vecs = number_vehicles
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.C = relevant_customers
        self.N = [0] + relevant_customers
        self.K = [k for k in range(self.num_vecs)]
        self.T = T
