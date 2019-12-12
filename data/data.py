import collections
import os, sys
import numpy as np
import ruamel.yaml
# sys.path.append('\\\\apclara1\\ControlRoomApps\\OnlineModel')
# sys.path.append('\\\\apclara1\\ControlRoomApps\\OnlineModel\\MasterLattice')
sys.path.append(os.path.abspath(__file__+'/../../../OnlineModel/'))
import SimulationFramework.Framework as Fw
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
    # runParameterDict_post = collections.OrderedDict()
    # data_plot_parameters = collections.OrderedDict()
    # data_summary_plot_parameters = collections.OrderedDict()

    def __init__(self):
        object.__init__(self)
        self.my_name = "data"
        self.parameterDict = collections.OrderedDict()
        self.parameterDict['lattice'] = collections.OrderedDict()
        self.latticeDict = self.parameterDict['lattice']
        self.parameterDict['scan'] = collections.OrderedDict()
        self.scanDict = self.parameterDict['scan']
        self.scanDict['parameter_scan'] = False
        self.parameterDict['simulation'] = collections.OrderedDict()
        self.simulationDict = self.parameterDict['simulation']
        self.parameterDict['generator'] = collections.OrderedDict()
        self.generatorDict = self.parameterDict['generator']
        self.scannableParametersDict = collections.OrderedDict()
        self.Framework = Fw.Framework(directory=directory_summary, clean=False, verbose=True)
        self.Framework.loadSettings('Lattices/CLA10-BA1_OM.def')
        self.my_name = "data"
        self.get_data()
        self.initialise_data()

    def get_framework(self):
        return self.Framework

    def initialise_data(self):
        # [self.runParameterDict.update({key: value}) for key, value in zip(data_keys, data_v)]
        [self.latticeDict.update({key: value}) for key, value in self.quad_values.items()]
        [self.latticeDict.update({key: value}) for key, value in self.gun_values.items()]
        [self.latticeDict.update({key: value}) for key, value in self.l01_values.items()]
        [self.generatorDict.update({key: value}) for key, value in self.laser_values.items()]
        [self.generatorDict.update({key: value}) for key, value in self.charge_values.items()]
        [self.generatorDict.update({key: value}) for key, value in self.number_of_particles.items()]
        [self.generatorDict.update({key: value}) for key, value in self.cathode.items()]
        [self.simulationDict.update({key: value}) for key, value in self.space_charge.items()]
        [self.simulationDict.update({key: value}) for key, value in self.astra_run_number.items()]
        [self.simulationDict.update({key: value}) for key, value in self.tracking_code.items()]

    def initialise_scan(self):
        [self.scan_values.update({key: value}) for key, value in zip(scan_parameter_keys, scan_parameter_v)]

    def initialise_scan_parameters(self):
        [self.scan_parameter.update({key: value}) for key, value in zip(scan_keys, scan_v)]

    def hello(self):
        print(self.my_name + ' says hello')

    def get_data(self):
        self.scan_values = collections.OrderedDict()
        self.scan_parameter = collections.OrderedDict()
        self.quad_values = collections.OrderedDict()
        self.gun_values = collections.OrderedDict()
        self.l01_values = collections.OrderedDict()
        self.dipole_values = collections.OrderedDict()
        self.kicker_values = collections.OrderedDict()
        self.screen_values = collections.OrderedDict()
        self.solenoid_values = collections.OrderedDict()
        self.charge_values = collections.OrderedDict()
        self.laser_values = collections.OrderedDict()
        self.number_of_particles = collections.OrderedDict()
        self.cathode = collections.OrderedDict()
        self.space_charge = collections.OrderedDict()
        self.astra_run_number = collections.OrderedDict()
        self.tracking_code = collections.OrderedDict()
        # quad_values.update({key: value}) for key, value in zip(data_keys, data_v)

        for quad in self.Framework.getElementType('quadrupole'):
            self.quad_values.update({quad['objectname']: collections.OrderedDict()})
            self.quad_values[quad['objectname']].update({'type': 'quadrupole'})
            self.quad_values[quad['objectname']].update({'k1l': quad['k1l']})
        for cavity in self.Framework.getElementType('cavity'):
            if cavity['controller_name'] == "GUN10":
                self.gun_values.update({'CLA-LRG1-GUN-CAV': collections.OrderedDict()})
                self.gun_values['CLA-LRG1-GUN-CAV'].update({'type': 'cavity'})
                self.gun_values['CLA-LRG1-GUN-CAV'].update({'phase': cavity['phase']})
                # self.gun_values.update({'CLA-LRG1-GUN-CAV:PHASE': cavity['field_amplitude']})
                self.gun_values['CLA-LRG1-GUN-CAV'].update({'field_amplitude': cavity['field_amplitude']})
                # self.gun_values.update({'CLA-LRG1-GUN-CAV:AMP': cavity['field_amplitude']})
                self.gun_values.update({'CLA-LRG1-MAG-SOL-01': collections.OrderedDict()})
                self.gun_values['CLA-LRG1-MAG-SOL-01'].update({'type': 'solenoid'})
                self.gun_values['CLA-LRG1-MAG-SOL-01'].update({'cavity': cavity['objectname']})
                self.gun_values['CLA-LRG1-MAG-SOL-01'].update(
                    {'field_amplitude': cavity['sub_elements']['CLA-LRG1-MAG-SOL-01']['field_amplitude']})
                self.gun_values['CLA-LRG1-GUN-CAV'].update({'sub_elements': collections.OrderedDict()})
                self.gun_values['CLA-LRG1-GUN-CAV']['sub_elements'].update(
                    {'CLA-LRG1-MAG-SOL-01': collections.OrderedDict()})
                self.gun_values['CLA-LRG1-GUN-CAV']['sub_elements']['CLA-LRG1-MAG-SOL-01'].update(
                    {'field_amplitude': self.gun_values['CLA-LRG1-MAG-SOL-01']['field_amplitude']})
            # self.gun_values['CLA-LRG1-GUN-CAV'].update({'sub_elements': collections.OrderedDict()})
            # self.gun_values['CLA-LRG1-GUN-CAV']['sub_elements'].update({'CLA-LRG-GUN-SOL': cavity['sub_elements']['CLA-LRG1-GUN-SOL']['field_amplitude']})
            # self.gun_values.update({'CLA-LRG1-GUN-CAV:AMP': cavity['field_amplitude']})
            # self.gun_values.update({'CLA-LRG1-GUN-SOL:AMP': cavity['sub_elements']['CLA-LRG1-GUN-SOL']['field_amplitude']})
            elif cavity['controller_name'] == "L01":
                self.l01_values.update({'CLA-L01-CAV': collections.OrderedDict()})
                self.l01_values['CLA-L01-CAV'].update({'type': 'cavity'})
                self.l01_values['CLA-L01-CAV'].update({'phase': cavity['phase']})
                self.l01_values['CLA-L01-CAV'].update({'field_amplitude': cavity['phase']})
                self.l01_values.update({'CLA-L01-CAV-SOL-01': collections.OrderedDict()})
                self.l01_values['CLA-L01-CAV-SOL-01'].update({'type': 'solenoid'})
                self.l01_values['CLA-L01-CAV-SOL-01'].update({'cavity': cavity['objectname']})
                self.l01_values['CLA-L01-CAV-SOL-01'].update(
                    {'field_amplitude': cavity['sub_elements']['CLA-L01-CAV-SOL-01']['field_amplitude']})
                self.l01_values.update({'CLA-L01-CAV-SOL-02': collections.OrderedDict()})
                self.l01_values['CLA-L01-CAV-SOL-02'].update({'type': 'solenoid'})
                self.l01_values['CLA-L01-CAV-SOL-02'].update({'cavity': cavity['objectname']})
                self.l01_values['CLA-L01-CAV-SOL-02'].update(
                    {'field_amplitude': cavity['sub_elements']['CLA-L01-CAV-SOL-02']['field_amplitude']})
                self.l01_values['CLA-L01-CAV-SOL-01'].update({'sub_elements': collections.OrderedDict()})
                self.l01_values['CLA-L01-CAV-SOL-01']['sub_elements'].update(
                    {'CLA-L01-CAV-SOL-01': collections.OrderedDict()})
                self.l01_values['CLA-L01-CAV-SOL-01']['sub_elements']['CLA-L01-CAV-SOL-01'].update(
                    {'field_amplitude': self.l01_values['CLA-L01-CAV-SOL-01']['field_amplitude']})
                self.l01_values['CLA-L01-CAV-SOL-02'].update({'sub_elements': collections.OrderedDict()})
                self.l01_values['CLA-L01-CAV-SOL-02']['sub_elements'].update(
                    {'CLA-L01-CAV-SOL-02': collections.OrderedDict()})
                self.l01_values['CLA-L01-CAV-SOL-02']['sub_elements']['CLA-L01-CAV-SOL-02'].update(
                    {'field_amplitude': self.l01_values['CLA-L01-CAV-SOL-02']['field_amplitude']})
        self.charge_values.update({'charge': collections.OrderedDict()})
        self.charge_values['charge'].update({'type': 'generator'})
        self.charge_values['charge'].update({'value': self.Framework.generator.charge})
        self.number_of_particles.update({'number_of_particles': collections.OrderedDict()})
        self.number_of_particles['number_of_particles'].update({'value': self.Framework.generator.particles})
        self.number_of_particles['number_of_particles'].update({'type': 'generator'})
        self.cathode.update({'cathode': collections.OrderedDict()})
        self.cathode['cathode'].update({'type': 'generator'})
        self.cathode['cathode'].update({'value': self.Framework.generator.parameters['cathode']})
        self.space_charge.update({'space_charge': collections.OrderedDict()})
        self.space_charge['space_charge'].update({'type': 'generator'})
        self.space_charge['space_charge'].update({'value': False})
        self.astra_run_number.update({'astra_run_number': collections.OrderedDict()})
        self.astra_run_number['astra_run_number'].update({'type': 'generator'})
        self.astra_run_number['astra_run_number'].update({'astra_run_number': 101})
        self.laser_values.update({'dist_x': collections.OrderedDict()})
        self.laser_values['dist_x'].update({'type': 'generator'})
        self.laser_values['dist_x'].update({'value': self.Framework.generator.parameters['dist_x']})
        self.laser_values.update({'dist_y': collections.OrderedDict()})
        self.laser_values['dist_y'].update({'type': 'generator'})
        self.laser_values['dist_y'].update({'value': self.Framework.generator.parameters['dist_y']})
        self.laser_values.update({'dist_z': collections.OrderedDict()})
        self.laser_values['dist_z'].update({'type': 'generator'})
        self.laser_values['dist_z'].update({'value': self.Framework.generator.parameters['dist_z']})
        self.laser_values.update({'sig_x': collections.OrderedDict()})
        self.laser_values['sig_x'].update({'type': 'generator'})
        self.laser_values['sig_x'].update({'value': self.Framework.generator.parameters['sig_x']})
        self.laser_values.update({'sig_y': collections.OrderedDict()})
        self.laser_values['sig_y'].update({'type': 'generator'})
        self.laser_values['sig_y'].update({'value': self.Framework.generator.parameters['sig_y']})
        self.laser_values.update({'sig_clock': collections.OrderedDict()})
        self.laser_values['sig_clock'].update({'type': 'generator'})
        self.laser_values['sig_clock'].update({'value': self.Framework.generator.parameters['sig_clock']})
        self.tracking_code.update({'tracking_code':  collections.OrderedDict()})
