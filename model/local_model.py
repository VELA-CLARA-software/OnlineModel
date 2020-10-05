import os
import sys
import time
import stat
import numpy as np
from copy import deepcopy
import collections
import uuid

sys.path.append(os.path.abspath(__file__+'/../../'))
from data import data
import controller.run_parameters_parser as yaml_parser
# import controller.database_controller as dbc
import model.twissData as twissData
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
    data_dicts = ['generator'] + lattices.lattices + ['runs']
    # if data['scanDict']['parameter_scan']:
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
        # self.dbcontroller = dbc.DatabaseController()
        self.directoryname = ''

    def set_base_directory(self, directory):
        self.basedirectoryname = directory

    def run_twiss(self, directory):
        twiss_model = twissData.twissData(directory=self.basedirectoryname+'/'+directory, name=directory)
        twiss = twiss_model.run_script()
        return twiss

    def get_all_directory_names(self):
        return list(self.dbcontroller.get_all_run_ids())

    def close_connection(self):
        return self.client.close()

    def update_tracking_codes(self):
        for l in self.data.lattices:
            code = self.data.parameterDict[l]['tracking_code']['value']
            # print('Setting',l,'to',code)
            self.data.Framework.change_Lattice_Code(l, code)

    def update_CSR(self):
        for l in self.data.lattices:
            csr = self.data.parameterDict[l]['csr']['value']
            csr_bins = self.data.parameterDict[l]['csr_bins']['value']
            lattice = self.data.Framework[l]
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
        for l in self.data.lattices:
            lsc = self.data.parameterDict[l]['lsc']['value']
            lsc_bins = self.data.parameterDict[l]['lsc_bins']['value']
            lattice = self.data.Framework[l]
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

    def update_Wakefields(self):
        npart = int(self.data.parameterDict['generator']['number_of_particles']['value'])
        for l in self.data.lattices:
            if 'zwake' in self.data.parameterDict[l]:
                zwake = self.data.parameterDict[l]['zwake']['value'] if npart > 3 else False
                trwake = self.data.parameterDict[l]['trwake']['value'] if npart > 3 else False
                lattice = self.data.Framework[l]
                elements = lattice.elements.values()
                for e in elements:
                    e.longitudinal_wakefield_enable = zwake
                    e.transverse_wakefield_enable = trwake
                    e.allow_long_beam = True

    def clear_prefixes(self):
        for l in self.data.lattices:
            self.data.Framework[l].prefix = ''

    def run_script(self):
        success = True
        self.directoryname = ''
        # print('+++++++++++++++++ Start the script ++++++++++++++++++++++')
        self.yaml = create_yaml_dictionary(self.data)
        # del self.yaml['simulation']['directory']
        if self.are_settings_in_database(self.yaml):
            self.directoryname = self.get_run_id_for_settings(self.yaml)
        else:
            self.directoryname = self.create_random_directory_name()
        # print('+++++++++++++++++ Using directory ', 'test/'+self.directoryname, ' ++++++++++++++++++++++')
        if not self.are_settings_in_database(self.yaml):
            self.update_tracking_codes()
            self.update_CSR()
            self.update_LSC()
            self.update_Wakefields()
            self.clear_prefixes()
            closest_match, lattices_to_be_saved = self.dbcontroller.reader.find_lattices_that_dont_exist(self.yaml)
            if len(lattices_to_be_saved) > 0:
                start_lattice = lattices_to_be_saved[0]
                if closest_match is not False:
                    self.data.Framework[start_lattice].prefix = '../'+closest_match+'/'
                    self.data.runsDict['prefix'] = closest_match
                    # print('Setting',start_lattice,'prefix = ', closest_match)
                    self.data.runsDict['start_lattice'] = start_lattice
                self.yaml = create_yaml_dictionary(self.data)
                self.data.Framework.setSubDirectory(self.basedirectoryname+'/'+self.directoryname)
                self.modify_framework(scan=False)
                self.data.Framework.save_changes_file(filename=self.data.Framework.subdirectory+'/changes.yaml')
                # try:
                # self.data.Framework['CLA-S02'].file_block['output']['end_element'] = 'EBT-BA1-DIA-FCUP-01'
                self.data.Framework.track(startfile=start_lattice)#, endfile='CLA-S02')
                # except Exception as e:
                #     print('!!!! Error in Tracking - settings not saved !!!!')
                #     print(e)
                #     success = False
        return success

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
        self.data.Framework.defineASTRACommand(scaling=int(self.data.generatorDict['number_of_particles']['value']))
        if not os.name == 'nt':
            self.data.Framework.defineCSRTrackCommand(scaling=int(self.data.generatorDict['number_of_particles']['value']))
            self.data.Framework.define_gpt_command(scaling=int(self.data.generatorDict['number_of_particles']['value']))

        [self.update_framework_elements(self.data.parameterDict[l]) for l in self.data.lattices]
        if self.data.parameterDict[lattices.lattices[0]]['bsol_tracking']['value']:
            # This is the scaling factor for getting (approx) zero field on the cathode from the BSOL = -0.3462 * 90% (gives about 1% error on the emittance)
            self.data.Framework.modifyElement('CLA-LRG1-MAG-BSOL-01', 'field_amplitude', -0.3462 * 0.9 * self.data.Framework['CLA-LRG1-MAG-SOL-01']['field_amplitude'])
        if scan==True and type is not None:
            print(self.data.parameterDict[dictname][pv])
        self.update_laser_properties()

    def update_laser_properties(self):
        self.data.Framework.change_generator(str(self.data.generatorDict['tracking_code']['value']))
        self.data.Framework.generator.number_of_particles = int(2**(3*int(self.data.generatorDict['number_of_particles']['value'])))
        # Convert to nC
        self.data.Framework.generator.charge = 1e-12*float(self.data.generatorDict['charge']['value'])
        ### LONGITUDINAL ###
        if str(self.data.generatorDict['longitudinal_distribution']['value']) == "Plateau":
            # print('longitudinal plateau')
            self.data.Framework.generator.distribution_type_z = "p"
            self.data.Framework.generator.plateau_rise_time = self.data.generatorDict['plateau_rise_time']['value'] * 1e-12
            self.data.Framework.generator.plateau_bunch_length = self.data.generatorDict['sig_clock']['value'] * 1e-12
        elif str(self.data.generatorDict['longitudinal_distribution']['value']) == "Gaussian":
            # print('longitudinal gaussian')
            # We need to be in RMS seconds - here we convert from FWHM and divide by 1e12 from pico-seconds
            self.data.Framework.generator.distribution_type_z = "g"
            self.data.Framework.generator.sigma_t = float(self.data.generatorDict['sig_clock']['value']) / (2.35482) * 1e-12
            self.data.Framework.generator.guassian_cutoff_z = int(self.data.generatorDict['longitudinal_cutoff']['value'])
        elif str(self.data.generatorDict['longitudinal_distribution']['value']) == "Uniform":
            # print('longitudinal uniform')
            self.data.Framework.generator.distribution_type_z = "p"
            self.data.Framework.generator.plateau_rise_time = 0
            self.data.Framework.generator.plateau_bunch_length = self.data.generatorDict['sig_clock']['value'] * 1e-12
        ### TRANSVERSE ###
        if str(self.data.generatorDict['transverse_distribution']['value']) == "Gaussian":
            self.data.Framework.generator.distribution_type_x = "2DGaussian"
            self.data.Framework.generator.distribution_type_y = "2DGaussian"
            self.data.Framework.generator.guassian_cutoff_x = int(self.data.generatorDict['transverse_cutoff']['value'])
            self.data.Framework.generator.guassian_cutoff_y = int(self.data.generatorDict['transverse_cutoff']['value'])
        elif str(self.data.generatorDict['transverse_distribution']['value']) == "Radial":
            # If we are in uniform or plateau we need to set the correct ASTRA parameter
            self.data.Framework.generator.distribution_type_x = "radial"
            self.data.Framework.generator.distribution_type_y = "radial"
            self.data.Framework.generator.lx = self.data.generatorDict['spot_size']['value'] * 1e-3
            self.data.Framework.generator.ly = self.data.generatorDict['spot_size']['value'] * 1e-3
        self.data.Framework.generator.sigma_x = self.data.generatorDict['spot_size']['value'] * 1e-3
        self.data.Framework.generator.sigma_y = self.data.generatorDict['spot_size']['value'] * 1e-3
        ### Thermal Emittance in radians ###
        self.data.Framework.generator.thermal_emittance = self.data.generatorDict['thermal_emittance']['value'] * 1e-3
        ### Offsets in X and Y ###
        self.data.Framework.generator.offset_x = self.data.generatorDict['offset_x']['value'] * 1e-3
        self.data.Framework.generator.offset_y = self.data.generatorDict['offset_y']['value'] * 1e-3

    def create_random_directory_name(self):
        dirname = str(uuid.uuid4())
        # while dirname in self.dirnames.values():
        #     dirname = 'test/'+str(uuid.uuid4())
        return dirname

    def save_settings_to_database(self, yaml, directoryname):
        self.dbcontroller.save_settings_to_database(yaml, directoryname)

    def are_settings_in_database(self, yaml):
        return self.dbcontroller.are_settings_in_database(yaml)

    def get_run_id_for_settings(self, yaml):
        if self.are_settings_in_database(yaml):
            return self.dbcontroller.get_run_id_for_settings(yaml)
        else:
            return None

    def get_absolute_folder_location(self, directoryname):
        return os.path.abspath(__file__+'/../../'+self.basedirectoryname+'/'+directoryname)

    def create_subdirectory(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)

    def export_parameter_values_to_yaml_file(self, auto=False, filename=None, directory="."):
        if auto is True:
            filename = 'settings.yaml'
            directory = self.basedirectoryname+'/'+self.directoryname
        if filename is not None:
            # print('directory = ', directory, '   filename = ', filename, '\njoin = ', str(os.path.relpath(directory + '/' + filename)))
            self.create_subdirectory(directory)
            try:
                yaml_parser.write_parameter_output_file(str(os.path.relpath(directory + '/' + filename)), create_yaml_dictionary(self.data))
            except Exception as e:
                print('Can\'t write YAML file!', filename, directory)
                print(e)
        else:
            print( 'Failed to export, please provide a filename.')
            exit()

    def import_yaml(self, directoryname):
        return self.import_parameter_values_from_yaml_file(self.basedirectoryname+'/'+directoryname+'/settings.yaml')

    def import_parameter_values_from_yaml_file(self, filename):
        filename = filename[0] if isinstance(filename,tuple) else filename
        filename = str(filename)
        if not filename == '' and not filename is None and (filename[-4:].lower() == '.yml' or filename[-5:].lower() == '.yaml'):
            # print('yaml filename = ', filename)
            loaded_parameter_dict = yaml_parser.parse_parameter_input_file(filename)
            # print('yaml data = ', loaded_parameter_dict)
            return loaded_parameter_dict
        else:
            return {}
