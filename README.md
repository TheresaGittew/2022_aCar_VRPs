# 2022_aCar_VRPs
VRP-VBS for the acar operation

input_interface.py => python file used as proxy for important input
paramters, such as time per service, costs, time horizon lengths, etc.
To be replaced by an excel file in which the operator can enter key parameters.

Execute.py => python file you can use to execute a scenario for
the infos provided in the input_interface.py. You have to provide
further info about the particular scenario in the Execute.py file;
go to the bottom of that file for further info

fpvrp_GRB_Model_XL.py => VRP-VBS implemented with gurobipy, specifically,
Class VRP_VBS_Optimizer  which contains constraints, objective, variables. Also, a callback
function is defined.

CaseStudy_ScenarioCreator.py => used for the Master Thesis to compute Case Studies
for Côte d'Ivoire and Ethiopia

CaseStudy_Reader => file that you can use to read the outputs from
the Case Study and summarize it in an Excel file

Excel_Handler => interface between numerical results and excel

fpvrp_ParameterInputClasses => Core is an interface to provided GIS
parameter, Class "InputGISReader", which extracts the .csv files and
converts it into the suitable format for the VRP_VBS_Optimizer Class

fpvrp_PostProcessing => miscellaneous methods; amongst others a RouteValidator
that checks if routes contain subtours. Another method can check a solution 
and enhance the computed routes by exchanging  arcs

fpvrp_RouteVizualizer => method to plot obtained model solution values.
For each day, a plot is generated, showing used links, delivery quantities,
nodes, and routes.

Numerical_Experiments => file containing the framework for numerical experiments that have been
conducted as a part of the master thesis.






