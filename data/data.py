import collections

macro_particle ='macro_particle'
laser_pulse_length = 'laser_pulse_length'
spot_size = 'spot_size'
charge = 'charge'
gun_gradient = 'gun_gradient'
gun_phase = 'gun_phase'
linac_1_gradient= 'linac_1_gradient'
linac_1_phase= 'linac_1_phase'
bucking_coil_and_sol_strength = 'bucking_coil_and_sol_strength'
linac_1_sol1_strength = 'linac_1_sol1_strength'
linac_2_sol1_strength = 'linac_1_sol2_strength'
end_of_line = 'end_of_line'
injector_space_charge = 'injector_space_charge'
rest_of_line_space_charge = 'rest_of_line_space_charge'
s02_quad1_strength='s02_quad1_strength'
s02_quad2_strength='s02_quad2_strength'
s02_quad3_strength='s02_quad3_strength'
s02_quad4_strength='s02_quad4_strength'
vela_quad1_strength='vela_quad1_strength'
vela_quad2_strength='vela_quad2_strength'
vela_quad3_strength='vela_quad3_strength'
vela_quad4_strength='vela_quad4_strength'
vela_quad5_strength='vela_quad5_strength'
vela_quad6_strength='vela_quad6_strength'
c2v_quad1_strength='c2v_quad1_strength'
c2v_quad2_strength='c2v_quad2_strength'
c2v_quad3_strength='c2v_quad3_strength'
ba1_quad1_strength='ba1_quad1_strength'
ba1_quad2_strength='ba1_quad2_strength'
ba1_quad3_strength='ba1_quad3_strength'
ba1_quad4_strength='ba1_quad4_strength'
ba1_quad5_strength='ba1_quad5_strength'
ba1_quad6_strength='ba1_quad6_strength'
ba1_quad7_strength='ba1_quad7_strength'
directory = 'directory'
parameter_to_scan = 'parameter_scan_combo_box'
parameter_scan_from_value = 'parameter_scan_from_line_edit'
parameter_scan_to_value = 'parameter_scan_to_line_edit'
parameter_scan_step_size = 'parameter_scan_step_size_line_edit'


data_keys = [macro_particle,laser_pulse_length,spot_size,charge,gun_gradient,
             gun_phase, linac_1_gradient,linac_1_phase,bucking_coil_and_sol_strength,
             linac_1_sol1_strength, linac_2_sol1_strength,end_of_line,injector_space_charge,
             s02_quad1_strength, s02_quad2_strength,s02_quad3_strength,s02_quad4_strength,
             c2v_quad1_strength,c2v_quad2_strength,c2v_quad3_strength,
             vela_quad1_strength,vela_quad2_strength,vela_quad3_strength,vela_quad4_strength,
             vela_quad5_strength,vela_quad6_strength,ba1_quad1_strength,ba1_quad2_strength,
             ba1_quad3_strength,ba1_quad4_strength,ba1_quad5_strength,ba1_quad6_strength,
             ba1_quad7_strength,rest_of_line_space_charge, directory]

data_v = [1,3,0.25,0.25,71.5,5,21,-10,0.237,0.05,-0.05,337,'T',3.012,-4.719,-4.07,
          13.316,54.756,-46.099,55.974,20.743,-18.492,5.267,-5.527,6.721,8.891,-3.8,
          9.9,-11.5,5.0,-3.5,-3.5,2.5,'T','/home/qfi29231/B_1/']

scannable_data_list = [laser_pulse_length,spot_size,charge,gun_gradient,
					   gun_phase, linac_1_gradient,linac_1_phase,bucking_coil_and_sol_strength,
					   linac_1_sol1_strength, linac_2_sol1_strength, s02_quad1_strength,
					   s02_quad2_strength,s02_quad3_strength,s02_quad4_strength, c2v_quad1_strength,
					   c2v_quad2_strength,c2v_quad3_strength, vela_quad1_strength,vela_quad2_strength,
					   vela_quad3_strength,vela_quad4_strength, vela_quad5_strength,vela_quad6_strength,
					   ba1_quad1_strength,ba1_quad2_strength, ba1_quad3_strength,ba1_quad4_strength,
					   ba1_quad5_strength,ba1_quad6_strength, ba1_quad7_strength]

scan_qt_items_keys = [parameter_to_scan, parameter_scan_from_value, parameter_scan_to_value,
			 parameter_scan_step_size]

scan_qt_items_values = ['charge', 25, 75, 25]

scan_parameter_keys = ['parameter_scan', 'parameter_scan_from', 'parameter_scan_to', 'parameter_scan_step_size']

scan_parameter_v = ['', 0, 1, 0.1]

class Data(object):

	data_values = collections.OrderedDict()
	scan_values = collections.OrderedDict()
	scan_parameters = collections.OrderedDict()
	scan_parameter_list = scannable_data_list
	def __init__(self):
		object.__init__(self)
		self.my_name = "data"

	def initialise_data(self):
		[self.data_values.update({key: value}) for key, value in zip(data_keys, data_v)]
	
	def initialise_scan(self):
		[self.scan_values.update({key : value}) for key, value in zip(scan_parameter_keys, scan_parameter_v)]
	
	def initialise_scan_parameters(self):
		[self.scan_parameters.update({key : value}) for key, value in zip(scan_qt_items_keys, scan_qt_items_values)]
	
	def hello(self):
		print(self.my_name + ' says hello')
