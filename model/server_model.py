import os
import sys
import time
import stat
import numpy as np
from copy import deepcopy

sys.path.append(os.path.abspath(__file__+'/../../../OnlineModel/'))
sys.path.append(os.path.abspath(__file__+'/../../../SimFrame/'))
import SimulationFramework.Framework as Fw

class Model(object):

    def __init__(self, data=None, runno=1):
        self.generator_params = ['number_of_particles', 'dist_x', 'dist_y', 'dist_z', 'sig_x', 'sig_y', 'sig_z']
        self.scan_progress = -1
        self.data = data
        sddsindex = runno % 20
        self.Framework = Fw.Framework(directory='.', clean=False, verbose=False, sddsindex=sddsindex)
        print('self.Framework.master_lattice_location = ', self.Framework.master_lattice_location)
        # self.Framework.defineElegantCommand(location=[self.Framework.master_lattice_location+'Codes/elegant'])
        # os.environ['RPN_DEFNS'] = self.Framework.master_lattice_location+'Codes/defns.rpn'
        self.Framework.loadSettings('Lattices/CLA10-BA1_OM.def')

    def create_subdirectory(self):
        self.data.runParameterDict['directory_line_edit'] = self.data.runParameterDict['directory_line_edit'] + '/' if not self.data.runParameterDict['directory_line_edit'].endswith('/') else self.data.runParameterDict['directory_line_edit']
        self.check_if_directory_exists()

    def update_tracking_codes(self):
        for l, c in self.data.simulationDict['tracking_code'].items():
            self.Framework.change_Lattice_Code(l, c)

    def update_CSR(self):
        for l, c in self.data.simulationDict['csr'].items():
            lattice = self.Framework[l]
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
            lattice = self.Framework[l]
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
        self.update_tracking_codes()
        self.update_CSR()
        self.update_LSC()
        startLattice = self.data.simulationDict['starting_lattice']
        endLattice = self.data.simulationDict['final_lattice']
        self.Framework.setSubDirectory(str(self.data.parameterDict['simulation']['directory']))
        self.modify_framework(scan=False)
        self.Framework.save_changes_file(filename=self.Framework.subdirectory+'/changes.yaml')
        if self.data.simulationDict['track']:
            self.Framework.track(startfile=startLattice, endfile=endLattice)
        else:
            time.sleep(0.5)

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
        if self.data.parameterDict['simulation']['bsol_tracking']:
            self.Framework.modifyElement('CLA-LRG1-MAG-BSOL-01', 'field_amplitude', -0.3462 * 0.9 * self.Framework['CLA-LRG1-MAG-SOL-01']['field_amplitude'])
        if scan==True and type is not None:
            print(self.data.parameterDict[dictname][pv])
        self.Framework.generator.number_of_particles = int(2**(3*int(self.data.generatorDict['number_of_particles']['value'])))
        self.Framework.generator.charge = 1e-9*float(self.data.generatorDict['charge']['value'])
        self.Framework.generator.sig_clock = float(self.data.generatorDict['sig_clock']['value']) / (2354.82)
        self.Framework.generator.sig_x = self.data.generatorDict['spot_size']['value']
        self.Framework.generator.sig_y = self.data.generatorDict['spot_size']['value']
