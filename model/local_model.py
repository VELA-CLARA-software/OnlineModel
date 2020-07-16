import os
import sys
import time
import stat
import numpy as np
from copy import deepcopy
import collections
import uuid

# sys.path.append(os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'data'))
# from data import data
sys.path.append(os.path.abspath(__file__+'/../../'))
from data import data
import controller.run_parameters_parser as yaml_parser
import database.database_controller as dbc
import model.twissData as twissData

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
    data_dicts = ['generator', 'INJ', 'S02', 'C2V', 'EBT', 'BA1', 'simulation']
    if data['scanDict']['parameter_scan']:
        data_dicts.append('scan')
    for n in data_dicts:
        export_dict = convert_data_types(export_dict, data['parameterDict'][n], n)
    return export_dict

class Model(object):
    output_directory = 'C:/Users/ujo48515/Documents/'
    width = 1000
    height = 600
    def __init__(self):
        self.path_exists = False
        self.data = data.Data()
        self.generator_params = ['number_of_particles', 'dist_x', 'dist_y', 'dist_z', 'sig_x', 'sig_y', 'sig_z']
        self.scan_progress = -1
        self.dbcontroller = dbc.DatabaseController()

    def run_twiss(self, directory):
        twiss_model = twissData.twissData(directory='test/'+directory, name=directory)
        twiss = twiss_model.run_script()
        return twiss

    def get_all_directory_names(self):
        return list(self.dbcontroller.get_all_run_ids())

    def close_connection(self):
        return self.client.close()

    def update_tracking_codes(self):
        for l, c in self.data.simulationDict['tracking_code'].items():
            self.data.Framework.change_Lattice_Code(l, c)

    def update_CSR(self):
        for l, c in self.data.simulationDict['csr'].items():
            lattice = self.data.Framework[l]
            elements = lattice.elements.values()
            for e in elements:
                e.csr_enable = c
                e.sr_enable = c
                e.isr_enable = c
                e.csr_bins = self.data.simulationDict['csr_bins'][l]
                e.current_bins = 0
                e.longitudinal_wakefield_enable = c
                e.transverse_wakefield_enable = c
            lattice.csrDrifts = c

    def update_LSC(self):
        for l, c in self.data.simulationDict['lsc'].items():
            lattice = self.data.Framework[l]
            elements = lattice.elements.values()
            for e in elements:
                e.lsc_enable = c
                e.lsc_bins = self.data.simulationDict['lsc_bins'][l]
            #     e.smoothing_half_width = 1
            #     e.lsc_high_frequency_cutoff_start = -1#0.25
            #     e.lsc_high_frequency_cutoff_end = -1#0.33
            # lattice.lsc_high_frequency_cutoff_start = -1#0.25
            # lattice.lsc_high_frequency_cutoff_end = -1#0.33
            lattice.lsc_bins = self.data.simulationDict['lsc_bins'][l]
            lattice.lscDrifts = c

    def run_script(self):
        print('+++++++++++++++++ Start the script ++++++++++++++++++++++')
        self.yaml = create_yaml_dictionary(self.data)
        del self.yaml['simulation']['directory']
        if self.are_settings_in_database(self.yaml):
            self.directoryname = self.get_run_id_for_settings(self.yaml)
        else:
            self.directoryname = self.create_random_directory_name()
        print('+++++++++++++++++ Using directory ', 'temp/'+self.directoryname, ' ++++++++++++++++++++++')
        if not self.are_settings_in_database(self.yaml):
            self.update_tracking_codes()
            self.update_CSR()
            self.update_LSC()
            startLattice = self.data.simulationDict['starting_lattice']
            endLattice = self.data.simulationDict['final_lattice']
            self.data.Framework.setSubDirectory('temp/'+self.directoryname)
            self.modify_framework(scan=False)
            self.data.Framework.save_changes_file(filename=self.data.Framework.subdirectory+'/changes.yaml')
            if self.data.simulationDict['track']:
                self.data.Framework.track(startfile=startLattice, endfile=endLattice)
            else:
                time.sleep(0.5)
            print(' now saving the settings... ')

    def get_directory_name(self):
        return self.directoryname

    ##### Find Starting Filename based on z-position ####
    def find_starting_lattice(self, z):
        lattices = self.data.Framework.latticeObjects.values()
        for l in lattices:
            for e in l.elements:
                    if e.position_end[2] <= z:
                        return l
        return 'generator'

    def update_framework_elements(self, inputdict):
        for key, value in inputdict.items():
            if isinstance(value, dict):
                if inputdict[key]['type'] == 'quadrupole':
                    self.data.Framework.modifyElement(key, 'k1l', float(value['k1l']))
                elif inputdict[key]['type'] == 'cavity':
                    self.data.Framework.modifyElement(key, 'field_amplitude', 1e6*float(value['field_amplitude']))
                    self.data.Framework.modifyElement(key, 'phase', value['phase'])
                elif inputdict[key]['type'] == 'solenoid':
                    if 'BSOL' in key:
                        self.data.Framework.modifyElement(key, 'field_amplitude', 0.3462 * float(value['field_amplitude']))
                    else:
                        self.data.Framework.modifyElement(key, 'field_amplitude', float(value['field_amplitude']))

    def modify_framework(self, scan=False, type=None, modify=None, cavity_params=None, generator_param=None):
        if not os.name == 'nt':
            self.data.Framework.defineASTRACommand(scaling=int(self.data.generatorDict['number_of_particles']['value']))
            self.data.Framework.defineCSRTrackCommand(scaling=int(self.data.generatorDict['number_of_particles']['value']))
            self.data.Framework.define_gpt_command(scaling=int(self.data.generatorDict['number_of_particles']['value']))

        [self.update_framework_elements(self.data.parameterDict[l]) for l in self.data.lattices]
        if self.data.parameterDict['simulation']['bsol_tracking']:
            self.data.Framework.modifyElement('CLA-LRG1-MAG-BSOL-01', 'field_amplitude', -0.3462 * 0.9 * self.data.Framework['CLA-LRG1-MAG-SOL-01']['field_amplitude'])
        if scan==True and type is not None:
            print(self.data.parameterDict[dictname][pv])
        self.data.Framework.generator.number_of_particles = int(2**(3*int(self.data.generatorDict['number_of_particles']['value'])))
        self.data.Framework.generator.charge = 1e-9*float(self.data.generatorDict['charge']['value'])
        self.data.Framework.generator.sig_clock = float(self.data.generatorDict['sig_clock']['value']) / (2354.82)
        self.data.Framework.generator.sig_x = self.data.generatorDict['spot_size']['value']
        self.data.Framework.generator.sig_y = self.data.generatorDict['spot_size']['value']

    def create_random_directory_name(self):
        dirname = str(uuid.uuid4())
        # while dirname in self.dirnames.values():
        #     dirname = 'test/'+str(uuid.uuid4())
        return dirname

    def save_settings_to_database(self, yaml, directoryname):
        self.dbcontroller.save_settings_to_database(yaml, directoryname)
        self.dbcontroller.save_run_information(directoryname, time.time(), os.getlogin())

    def are_settings_in_database(self, yaml):
        return self.dbcontroller.are_settings_in_database(yaml)

    def get_run_id_for_settings(self, yaml):
        if self.are_settings_in_database(yaml):
            return self.dbcontroller.get_run_id_for_settings(yaml)
        else:
            return None

    def get_absolute_folder_location(self, directoryname):
        return os.path.abspath(__file__+'/../../test/'+directoryname)