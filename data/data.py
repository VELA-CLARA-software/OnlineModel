import collections

astra_run_number = 'astra_run_number_line_edit'
macro_particle = 'macro_particle_line_edit'
laser_pulse_length = 'laser_pulse_length_line_edit'
spot_size = 'spot_size_line_edit'
charge = 'charge_line_edit'
gun_gradient = 'gun_gradient_line_edit'
gun_phase = 'gun_phase_line_edit'
linac_1_gradient = 'linac_1_gradient_line_edit'
linac_1_phase = 'linac_1_phase_line_edit'
bucking_coil_and_sol_strength = 'bucking_coil_and_sol_strength_line_edit'
linac_1_sol1_strength = 'linac_1_sol1_strength_line_edit'
linac_2_sol1_strength = 'linac_1_sol2_strength_line_edit'
end_of_line = 'end_of_line_line_edit'
injector_space_charge = 'injector_space_charge_check_box'
rest_of_line_space_charge = 'rest_of_line_space_charge_check_box'
s02_quad1_strength = 's02_quad1_strength_line_edit'
s02_quad2_strength = 's02_quad2_strength_line_edit'
s02_quad3_strength = 's02_quad3_strength_line_edit'
s02_quad4_strength = 's02_quad4_strength_line_edit'
vela_quad1_strength = 'vela_quad1_strength_line_edit'
vela_quad2_strength = 'vela_quad2_strength_line_edit'
vela_quad3_strength = 'vela_quad3_strength_line_edit'
vela_quad4_strength = 'vela_quad4_strength_line_edit'
vela_quad5_strength = 'vela_quad5_strength_line_edit'
vela_quad6_strength = 'vela_quad6_strength_line_edit'
c2v_quad1_strength = 'c2v_quad1_strength_line_edit'
c2v_quad2_strength = 'c2v_quad2_strength_line_edit'
c2v_quad3_strength = 'c2v_quad3_strength_line_edit'
ba1_quad1_strength = 'ba1_quad1_strength_line_edit'
ba1_quad2_strength = 'ba1_quad2_strength_line_edit'
ba1_quad3_strength = 'ba1_quad3_strength_line_edit'
ba1_quad4_strength = 'ba1_quad4_strength_line_edit'
ba1_quad5_strength = 'ba1_quad5_strength_line_edit'
ba1_quad6_strength = 'ba1_quad6_strength_line_edit'
ba1_quad7_strength = 'ba1_quad7_strength_line_edit'
directory = 'directory_line_edit'

parameter_to_scan = 'parameter_scan_combo_box'
parameter_scan_from_value = 'parameter_scan_from_line_edit'
parameter_scan_to_value = 'parameter_scan_to_line_edit'
parameter_scan_step_size = 'parameter_scan_step_size_line_edit'
parameter_scan = 'parameter_scan_check_box'
# Post-processing dictionary
directory_post = 'directory_post_line_edit'
directory_run_post_1 = 'directory_post_combo_box'
directory_run_post_2 = 'directory_post_combo_box_2'
directory_run_post_3 = 'directory_post_combo_box_3'
directory_run_post_4 = 'directory_post_combo_box_4'

# Summary post-processing dictionary
directory_summary = 'directory_summary_line_edit'
summary_save_plot = 'summary_save_plot_check_box'
summary_output_file = 'summary_output_file_line_edit'
data_keys = [astra_run_number, macro_particle, laser_pulse_length, spot_size, charge, gun_gradient,
             gun_phase, linac_1_gradient, linac_1_phase, bucking_coil_and_sol_strength,
             linac_1_sol1_strength, linac_2_sol1_strength, end_of_line, injector_space_charge,
             s02_quad1_strength, s02_quad2_strength, s02_quad3_strength, s02_quad4_strength,
             c2v_quad1_strength, c2v_quad2_strength, c2v_quad3_strength,
             vela_quad1_strength, vela_quad2_strength, vela_quad3_strength, vela_quad4_strength,
             vela_quad5_strength, vela_quad6_strength, ba1_quad1_strength, ba1_quad2_strength,
             ba1_quad3_strength, ba1_quad4_strength, ba1_quad5_strength, ba1_quad6_strength,
             ba1_quad7_strength, rest_of_line_space_charge, directory]

data_keys_post = [directory_post, directory_run_post_1, directory_run_post_2,directory_run_post_3,directory_run_post_4]
data_keys_post_summary = [directory_summary, summary_save_plot, summary_output_file]

post_scan_plot_keys = ['emittance (x)', 'emittance (y)', 'emittance (z)', 'rms (x)', 'rms (y)', 'rms (z)',
                       'Average (x)', 'Average (y)', 'Energy spread', 'Kinetic Energy']
post_scan_plot_v = ['emitt', 'emitt', 'emitt', 'bs', 'bs', 'bl', 'av', 'av', 'rmsespread', 'ke']

data_v = [101, 1, 3, 0.25, 0.25, 120, -9, 21, -16, 0.345, 0.05, -0.05, 337, 'T', 3.012, -4.719, -4.07,
          13.316, 54.756, -46.099, 55.974, 20.743, -18.492, 5.267, -5.527, 6.721, 8.891, -3.8,
          9.9, -11.5, 5.0, -3.5, -3.5, 2.5, 'T', '/home/qfi29231/B_1/']

data_v_post = ['', '', '', '', '']
data_v_summary = ['', '', '']

scannable_data_list = [laser_pulse_length, spot_size, charge, gun_gradient,
                       gun_phase, linac_1_gradient, linac_1_phase, bucking_coil_and_sol_strength,
                       linac_1_sol1_strength, linac_2_sol1_strength, s02_quad1_strength,
                       s02_quad2_strength, s02_quad3_strength, s02_quad4_strength, c2v_quad1_strength,
                       c2v_quad2_strength, c2v_quad3_strength, vela_quad1_strength, vela_quad2_strength,
                       vela_quad3_strength, vela_quad4_strength, vela_quad5_strength, vela_quad6_strength,
                       ba1_quad1_strength, ba1_quad2_strength, ba1_quad3_strength, ba1_quad4_strength,
                       ba1_quad5_strength, ba1_quad6_strength, ba1_quad7_strength]

scan_keys = [parameter_scan, parameter_to_scan, parameter_scan_from_value, parameter_scan_to_value,
             parameter_scan_step_size]

scan_v = [True, 'charge', 25, 75, 25]

scan_parameter_keys = ['parameter_scan', 'parameter_scan_from', 'parameter_scan_to', 'parameter_scan_step_size']

scan_parameter_v = ['', 0, 1, 0.1]


class Data(object):
    data_values = collections.OrderedDict()
    scan_values = collections.OrderedDict()
    scan_parameter = collections.OrderedDict()
    scan_parameter_list = scannable_data_list
    data_values_post = collections.OrderedDict()
    data_plot_parameters = collections.OrderedDict()
    data_summary_plot_parameters = collections.OrderedDict()

    def __init__(self):
        object.__init__(self)
        self.my_name = "data"

    def initialise_data(self):
        [self.data_values.update({key: value}) for key, value in zip(data_keys, data_v)]

    def initialise_scan(self):
        [self.scan_values.update({key : value}) for key, value in zip(scan_parameter_keys, scan_parameter_v)]

    def initialise_scan_parameters(self):
        [self.scan_parameter.update({key : value}) for key, value in zip(scan_keys, scan_v)]

    def initialise_data_post(self):
        [self.data_values_post.update({key: value}) for key, value in zip(data_keys_post, data_v_post)]
        [self.data_plot_parameters.update({key: value}) for key, value in zip(post_scan_plot_keys, post_scan_plot_v)]
        self.data_values_post['directory_post_line_edit'] = self.data_values['directory_line_edit']

    def initialise_data_summary_post(self):
        [self.data_summary_plot_parameters.update({key:value}) for key, value in zip(data_keys_post_summary, data_v_summary)]
    #def initialise_data(self):
    #    for key_dict, d_key, d_val in zip(['data_values', 'scan_values', 'scan_parameter', 'data_values_post'],
    #                                      ['data_v', 'scan_parameter_v', 'scan_v', 'data_v_post'],
    #                                      ['data_keys', 'scan_parameter_keys', 'scan_keys', 'data_keys_post']):  # type: (str, str, str)
    #        for key, value in zip(d_key, d_val):
    #            getattr(self, key_dict).update({key: value})

    def hello(self):
        print(self.my_name + ' says hello')

