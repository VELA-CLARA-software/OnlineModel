import collections
import view as view
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


# data_keys_post = [directory_post, directory_run_post_1, directory_run_post_2,directory_run_post_3,directory_run_post_4]
# data_keys_post_summary = [directory_summary, summary_save_plot, summary_output_file]

# post_scan_plot_keys = ['emittance (x)', 'emittance (y)', 'emittance (z)', 'rms (x)', 'rms (y)', 'rms (z)',
                       # 'Average (x)', 'Average (y)', 'Energy spread', 'Kinetic Energy']
# post_scan_plot_v = ['emitt', 'emitt', 'emitt', 'bs', 'bs', 'bl', 'av', 'av', 'rmsespread', 'ke']



class Data(object):

    # scan_values = collections.OrderedDict()
    # scan_parameter = collections.OrderedDict()
    # scan_parameter_list = scannable_data_list
    # data_values_post = collections.OrderedDict()
    # data_plot_parameters = collections.OrderedDict()
    # data_summary_plot_parameters = collections.OrderedDict()

    def __init__(self):
        object.__init__(self)
        self.my_name = "data"
        self.runParameterDict = collections.OrderedDict()
        self.parameterScanDict = collections.OrderedDict()
        self.directoryDict = collections.OrderedDict()
        self.scannableParametersDict = collections.OrderedDict()

    # def initialise_data_post(self):
        # [self.data_values_post.update({key: value}) for key, value in zip(data_keys_post, data_v_post)]
        # [self.data_plot_parameters.update({key: value}) for key, value in zip(post_scan_plot_keys, post_scan_plot_v)]
        # self.data_values_post['directory_post_line_edit'] = self.data_values['directory_line_edit']

    # def initialise_data_summary_post(self):
        # [self.data_summary_plot_parameters.update({key:value}) for key, value in zip(data_keys_post_summary, data_v_summary)]
    # #def initialise_data(self):
    # #    for key_dict, d_key, d_val in zip(['data_values', 'scan_values', 'scan_parameter', 'data_values_post'],
    # #                                      ['data_v', 'scan_parameter_v', 'scan_v', 'data_v_post'],
    # #                                      ['data_keys', 'scan_parameter_keys', 'scan_keys', 'data_keys_post']):  # type: (str, str, str)
    # #        for key, value in zip(d_key, d_val):
    # #            getattr(self, key_dict).update({key: value})

    # def hello(self):
        # print(self.my_name + ' says hello')
