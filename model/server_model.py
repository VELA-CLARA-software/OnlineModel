import os
import sys
import time
import stat
import numpy as np
from copy import deepcopy
import collections
import glob

sys.path.append(os.path.abspath(__file__+'/../../../OnlineModel/'))
sys.path.append(os.path.abspath(__file__+'/../../../SimFrame/'))
import SimulationFramework.Framework as Fw
sys.path.append(os.path.abspath(__file__+'/../../'))
import controller.run_parameters_parser as yaml_parser
import database.database_controller as dbc
import data.lattices as lattices

def convert_data_types( export_dict={}, data_dict={}, keyname=None):
    if keyname is not None:
        export_dict[keyname] = dict()
        edict = export_dict[keyname]
    else:
        edict = export_dict
    for key, value in data_dict.items():
        if isinstance(value, (dict, collections.OrderedDict)) and not key == 'sub_elements':
            subdict = convert_data_types({}, value)
            edict.update({key:subdict})
        else:
            if not key == 'sub_elements':
                # value = self.model.data.Framework.convert_numpy_types(value)
                edict.update({key:value})
    return export_dict

def create_yaml_dictionary(data):
    export_dict = dict()
    print(type(data))
    data_dicts = ['generator'] + lattices.lattices
    if data['scanDict']['parameter_scan']:
        export_dict = convert_data_types(export_dict, data['scanDict'], 'scan')
    export_dict = convert_data_types(export_dict, data['runsDict'], 'runs')
    for n in data_dicts:
        export_dict = convert_data_types(export_dict, data['parameterDict'][n], n)
    return export_dict

class Model(object):

    def __init__(self, directoryname, data, dbcontroller, runno=1):
        self.generator_params = ['number_of_particles', 'dist_x', 'dist_y', 'dist_z', 'sig_x', 'sig_y', 'sig_z']
        self.scan_progress = -1
        self.data = data
        self.directoryname = directoryname
        sddsindex = runno % 20
        self.Framework = Fw.Framework(directory='.', clean=False, verbose=False, sddsindex=sddsindex)
        # print('self.Framework.master_lattice_location = ', self.Framework.master_lattice_location)
        # self.Framework.defineElegantCommand(location=[self.Framework.master_lattice_location+'Codes/elegant'])
        # os.environ['RPN_DEFNS'] = self.Framework.master_lattice_location+'Codes/defns.rpn'
        self.Framework.loadSettings(lattices.lattice_definition)
        self.lattices = lattices.lattices
        self.dbcontroller = dbcontroller

    def create_subdirectory(self):
        self.data.runParameterDict['directory_line_edit'] = self.data.runParameterDict['directory_line_edit'] + '/' if not self.data.runParameterDict['directory_line_edit'].endswith('/') else self.data.runParameterDict['directory_line_edit']
        self.check_if_directory_exists()

    def update_tracking_codes(self):
        for l in self.data.lattices:
            code = self.data.parameterDict[l]['tracking_code']['value']
            self.Framework.change_Lattice_Code(l, code)

    def update_CSR(self):
        for l in self.lattices:
            csr = self.data.parameterDict[l]['csr']['value']
            csr_bins = self.data.parameterDict[l]['csr_bins']['value']
            lattice = self.Framework[l]
            elements = lattice.elements.values()
            for e in elements:
                e.csr_enable = csr
                e.sr_enable = csr
                e.isr_enable = csr
                e.csr_bins = csr_bins
                e.current_bins = 0
                e.longitudinal_wakefield_enable = csr
                e.transverse_wakefield_enable = csr
            lattice.csrDrifts = csr

    def update_LSC(self):
        for l in self.lattices:
            lsc = self.data.parameterDict[l]['lsc']['value']
            lsc_bins = self.data.parameterDict[l]['lsc_bins']['value']
            lattice = self.Framework[l]
            elements = lattice.elements.values()
            for e in elements:
                e.lsc_enable = lsc
                e.lsc_bins = lsc_bins
            #     e.smoothing_half_width = 1
            #     e.lsc_high_frequency_cutoff_start = -1#0.25
            #     e.lsc_high_frequency_cutoff_end = -1#0.33
            # lattice.lsc_high_frequency_cutoff_start = -1#0.25
            # lattice.lsc_high_frequency_cutoff_end = -1#0.33
            lattice.lsc_bins = lsc_bins
            lattice.lscDrifts = lsc

    def clear_prefixes(self):
        for l in self.lattices:
            self.Framework[l].prefix = ''

    def run_script(self):
        print('+++++++++++++++++ Start the script ++++++++++++++++++++++')
        self.yaml = create_yaml_dictionary(self.data)
        self.update_tracking_codes()
        self.update_CSR()
        self.update_LSC()
        self.clear_prefixes()
        closest_match, lattices_to_be_saved = self.dbcontroller.reader.find_lattices_that_dont_exist(self.yaml)
        if len(lattices_to_be_saved) > 0:
            start_lattice = lattices_to_be_saved[0]
            if closest_match is not False:
                self.Framework[start_lattice].prefix = '../'+closest_match+'/'
                self.data.runsDict['prefix'] = closest_match
            self.data.runsDict['start_lattice'] = start_lattice
            self.yaml = create_yaml_dictionary(self.data)
            self.Framework.setSubDirectory(self.directoryname)
            self.modify_framework(scan=False)
            self.Framework.save_changes_file(filename=self.Framework.subdirectory+'/changes.yaml')
            if self.data.runsDict['track']:
                self.Framework.track(startfile=start_lattice)#, endfile=endLattice)
            else:
                time.sleep(0.5)
        self.Framework.progress = 100
            # print(' now saving the settings... ')

    ##### Find Starting Filename based on z-position ####
    def find_starting_lattice(self, z):
        lattices = self.Framework.latticeObjects.values()
        for l in lattices:
            for e in l.elements:
                    if e.position_end[2] <= z:
                        return l
        return 'generator'

    def update_framework_elements(self, inputdict):
        for key, value in inputdict.items():
            if isinstance(value, dict):
                if inputdict[key]['type'] == 'quadrupole':
                    self.Framework.modifyElement(key, 'k1l', float(value['k1l']))
                elif inputdict[key]['type'] == 'cavity':
                    self.Framework.modifyElement(key, 'field_amplitude', 1e6*float(value['field_amplitude']))
                    self.Framework.modifyElement(key, 'phase', value['phase'])
                elif inputdict[key]['type'] == 'solenoid':
                    if 'BSOL' in key:
                        self.Framework.modifyElement(key, 'field_amplitude', 0.3462 * float(value['field_amplitude']))
                    else:
                        self.Framework.modifyElement(key, 'field_amplitude', float(value['field_amplitude']))

    def modify_framework(self, scan=False, type=None, modify=None, cavity_params=None, generator_param=None):
        if not os.name == 'nt':
            self.Framework.defineASTRACommand(scaling=int(self.data.generatorDict['number_of_particles']['value']))
            self.Framework.defineCSRTrackCommand(scaling=int(self.data.generatorDict['number_of_particles']['value']))
            self.Framework.define_gpt_command(scaling=int(self.data.generatorDict['number_of_particles']['value']))

        [self.update_framework_elements(self.data.parameterDict[l]) for l in self.data.lattices]
        if self.data.parameterDict[lattices.lattices[0]]['bsol_tracking']['value']:
            self.Framework.modifyElement('CLA-LRG1-MAG-BSOL-01', 'field_amplitude', -0.3462 * 0.9 * self.Framework['CLA-LRG1-MAG-SOL-01']['field_amplitude'])
        if scan==True and type is not None:
            print(self.data.parameterDict[dictname][pv])
        self.Framework.generator.number_of_particles = int(2**(3*int(self.data.generatorDict['number_of_particles']['value'])))
        self.Framework.generator.charge = 1e-9*float(self.data.generatorDict['charge']['value'])
        self.Framework.generator.sig_clock = float(self.data.generatorDict['sig_clock']['value']) / (2354.82)
        self.Framework.generator.sig_x = self.data.generatorDict['spot_size']['value']
        self.Framework.generator.sig_y = self.data.generatorDict['spot_size']['value']

    def create_subdirectory(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)

    def export_parameter_values_to_yaml_file(self):
        directory = self.directoryname
        filename = 'settings.yaml'
        if not filename == "":
            print('directory = ', directory, '   filename = ', filename, '\njoin = ', str(os.path.relpath(directory + '/' + filename)))
            self.create_subdirectory(directory)
            export_dict = create_yaml_dictionary(self.data)
            yaml_parser.write_parameter_output_file(str(os.path.relpath(directory + '/' + filename)), export_dict)
        else:
            print( 'Failed to export, please provide a filename.')
