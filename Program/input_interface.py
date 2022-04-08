class DummyForExcelInterface_ET:

    def __init__(self):
        self.num_days = 5
        self.T = [i for i in range(self.num_days)]
        self.S = ['WDS', 'ELEC', 'PNC']
        self.H = [0, 1]
        self.Q_h_s = {(0, 'WDS'): 1000, (0, 'ELEC'): 100, (0, 'PNC'): 20,
                      (1, 'WDS'): 750, (1, 'ELEC'): 300, (1, 'PNC'): 10}
        self.fixed_costs = {0: 70000, 1: 65000}

        self.service_times = {'WDS': 0.0001, 'PNC': 0.1666, 'ELEC': 0.001}

        self.daily_demand_factors = {'WDS': 1, 'ELEC': 1, 'ED': 1, 'PNC': 1},
        self.functions_to_consumption_per_T = {'WDS': (lambda x: x * 0.25), 'ELEC': (lambda x: x * 0.03),
                                          'ED': (lambda x: x * 0.25), 'PNC': (lambda y: y * 3 / 52)}
        #self.max_num_vehicles = 25


    def get_vehiclecapa_numdays_S(self):
        return self

class DummyForExcelInterface_IC:

    def __init__(self):
        self.num_days = 5
        self.T = [i for i in range(self.num_days)]
        self.S = ['ELEC', 'PNC']
        self.H = [0, 1]
        self.Q_h_s = { (0, 'ELEC'): 1800, (0, 'PNC'): 25,
                       (1, 'ELEC'): 1000, (1, 'PNC'): 25}

        self.fixed_costs = {0: 60000, 1: 50000}

        self.service_times = {'PNC': 0.166, 'ELEC': 0.00833333, 'ED':0.0833}

        self.daily_demand_factors = {'ELEC': 1, 'ED': 1, 'PNC': 1},
        self.functions_to_consumption_per_T = {'WDS': (lambda x: x * 3), 'ELEC': (lambda x: x * 1),
                                               'ED': (lambda x: x * 1), 'PNC': (lambda y: y * 3 / 52)}


    def get_vehiclecapa_numdays_S(self):
        return self