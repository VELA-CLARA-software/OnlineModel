import collections
import os, sys, time
import re
import numpy as np
import ruamel.yaml as yaml
sys.path.append(os.path.abspath(__file__+'/../../../OnlineModel/'))
sys.path.append(os.path.abspath(__file__+'/../../../SimFrame/'))
sys.path.append(os.path.abspath(__file__+'/../../'))
import SimulationFramework.Framework as Fw
import SimulationFramework.Modules.constants
import requests, json, datetime, math, numpy
import data.lattices as lattices
from data.DBURT_parser import DBURT_Parser
from copy import copy, deepcopy

from .parameters import parameterDict
from .parameters import screenDict

class Data(object):
    """Data object to hold all of the parameters and interface to the SimFrame framework."""

    def __getitem__(self, key):
        return getattr(self, key)

    def __init__(self, initialise=True):
        super(Data, self).__init__()
        """Initialise the Data object:
              - Create required dictionaries
              - Initialise the SimFrame framework object
              - Extract element data from the framework
              - Initialise dictionaries with the specified values
        """
        self.parser = DBURT_Parser()
        self.Framework = Fw.Framework(directory='.', clean=False, verbose=False, delete_output_files=False)
        self.Framework.loadSettings(lattices.lattice_definition)
        self.lattices = lattices.lattices

        if initialise: # When we are deep copying we don't need to do this, so don't...
            self.parameterDict = parameterDict()
            self.generatorDict = self.parameterDict['generator']
            self.runsDict = self.parameterDict['runs']
            self.scanDict = self.parameterDict['scan']
            self.screenDict = screenDict(self.Framework)

            self.get_data()
            self.initialise_data()

    def __deepcopy__(self, memo):
        """Only copy required objects."""
        start = time.time()
        datacopy = type(self)(initialise=False)
        start = time.time()
        datacopy.parameterDict = deepcopy(self.parameterDict, memo)
        datacopy.generatorDict = datacopy.parameterDict['generator']
        datacopy.runsDict = datacopy.parameterDict['runs']
        return datacopy

    def get_data(self):
        """Initialise element dictionaries and prepare them for the framework values."""
        self.scan_parameter = collections.OrderedDict()
        self.parameterDict.get_data(self.Framework)

    def initialise_data(self):
        """Initialise the element dictionaries and keys with data from the framework."""
        self.parameterDict.initialise_data()
        self.quad_values = self.parameterDict.quad_values
        self.rf_values = self.parameterDict.rf_values

    def initialise_scan(self, id):
        """Initialise the scan dictionary with relevant parameters."""
        self.scanDict[str(id)] = {}
        [self.scanDict[str(id)].update({key: None}) for key in ['scan', 'parameter', 'scan_from_value', 'scan_to_value', 'scan_step_size']]

    def initialise_scan_parameters(self):
        """Update the scan_parameter dictionary with relevant parameters."""
        [self.scan_parameter.update({key: value}) for key, value in zip(scan_keys, scan_v)]

    def get_pv_alias(self, dict, name, param=None, rf_type=None):
        """Return the PV alias for a given dictionary entry."""
        if dict[name]['type'] == 'quadrupole':
            dict[name].update({"pv_suffix_alias": "SETI"})
            return "SETI"
        elif dict[name]['type'] == 'solenoid':
            dict[name].update({"pv_suffix_alias": "SETI"})
            return "SETI"
        elif dict[name]['type'] == "cavity" and rf_type is not None:
            if param == "phase":
                dict[name].update({"pv_phase_alias": "vm:dsp:sp_ph:phase"})
                return "vm:dsp:sp_ph:phase"
            elif param == "field_amplitude":
                dict[name].update({"pv_field_amplitude_alias": "ad1:ch6:power_remote_s.POWER"})
                return "ad1:ch6:power_remote_s.POWER"
        elif dict[name]['type'] == "generator" and param is not None:
            if param == "charge":
                dict[name].update({"pv_root_alias": "CLA-S01-DIA-WCM-01"})
                dict[name].update({"pv_suffix_alias": "Q"})
                return "Q"

    def read_values_from_archiver(self, pv_name, time_from=None, time_to=None):
        """Extract values from the archiver for a given PV."""
        # NOTE: time_from and time_to must be in ISO 1806 format!!
        # see http://claraserv2.dl.ac.uk/cssi_wiki/doku.php/archiver:pulling_data?s[]=archiver
        if time_from is None:
            time_from = datetime.datetime.now().isoformat() + "Z"
        if time_to is None:
            time_to = datetime.datetime.now().isoformat() + "Z"
        url = "http://claraserv2.dl.ac.uk:17668/retrieval/data/getData.json?pv=" + pv_name + "&from=" + time_from + "&to=" + time_to
        # print(url)
        r = requests.get(url)
        data = r.json()
        value = numpy.mean(data[0]['data'][0]['val'])
        # print(value)
        return value

    def get_energy_gain(self, time_from=None, time_to=None):
        """Return the calculated energy gain for an RF structure based on timstamps in the archiver."""
        for l in self.lattices:
            for key, value in self.parameterDict[l].items():
                if value['type'] == 'cavity':
                    cavity_length = value['length']
                    pv_amp_alias = value['pv_root_alias'] + ":" + value['pv_field_amplitude_alias']
                    pv_phase_alias = value['pv_root_alias'] + ":" + value['pv_phase_alias']
                    forward_power = self.read_values_from_archiver(pv_amp_alias, time_from, time_to) * 10 ** 6
                    phase = 0 # self.read_values_from_archiver(pv_phase_alias, time_from, time_to)
                    if value['controller_name'] == "GUN10":
                        pulse_length = 2.5
                        gun_energy_gain = self.get_energy_from_rf(forward_power, phase, pulse_length) / cavity_length
                        value.update({'energy_gain': float(gun_energy_gain)})
                        value['field_amplitude'] = float(gun_energy_gain)
                    elif value['controller_name'] == "L01":
                        pulse_length = 0.75
                        l01_energy_gain = self.get_energy_from_rf(forward_power, phase, pulse_length) / cavity_length
                        value.update({'energy_gain': float(l01_energy_gain)})
                        value['field_amplitude'] = float(l01_energy_gain)
                    value['phase'] = phase
                    value['pulse_length'] = pulse_length
        fudge = 0
        total_energy_gain = gun_energy_gain + l01_energy_gain + fudge
        return total_energy_gain

    def generate_magnet_name(self, name):
        """Return fully formed magnet name based on the framework element name."""
        name_number = re.compile(r'(?P<name>[a-zA-Z]+)(?P<number>\d+)')
        name_nonumber = re.compile(r'(?P<name>[a-zA-Z]+)')
        split = name.split('-')
        if split[0] == 'INJ':
            lattice = 'EBT-INJ'
        elif split[0] == 'BA1':
            lattice = 'EBT-BA1'
        else:
            lattice = 'CLA-' + split[0]
        match = name_number.search(split[1])
        if match:
            name, number = match.group('name'), match.group('number').zfill(2)
            if 'QUAD' in name:
                return lattice, lattice + '-MAG-QUAD-' + number
            elif 'SOL' in name:
                return lattice, lattice + '-MAG-SOL-' + number
        if split[0] == 'LRG':
            match = name_nonumber.search(split[1])
            if match and match.group('name'):
                name = match.group('name')
                lattice = 'CLA-LRG1'
                if 'SOL' == name:
                    return 'Gun', lattice + '-MAG-SOL-01'
                elif 'BSOL' == name:
                    return 'Gun', lattice + '-MAG-BSOL-01'
        return None, None

    def read_values_from_DBURT(self, dburt):
        """Extrtact values from a DBURT file and update the dictionaries."""
        data = self.parser.parse_DBURT(dburt)
        magnetdata = {}
        speed_of_light = scipy.constants.speed_of_light / 1e6
        for key, mag in data['magnets'].items():
            mag['lattice'], mag['fullname'] = self.generate_magnet_name(mag['name'])
            if mag['lattice'] == 'CLA-L01':
                mag['lattice'] = 'Linac'
            if mag['lattice'] == 'Linac' or mag['lattice'] == 'Gun':
                self.total_energy_gain = 5
            else:
                self.total_energy_gain = 35
            if mag['fullname'] in self.quad_values:
                value = self.quad_values[mag['fullname']]
            elif mag['fullname'] in self.rf_values:
                value = self.rf_values[mag['fullname']]
            else:
                value = {'type': None}
            mag['value'] = value
            # print('fullname = ', self.generate_magnet_name(mag['name']))
        # for key, mag in data['magnets'].items():
            # value = mag['values']
            if value['type'] == 'quadrupole':
                quad_pv_alias = key + ":" + value['pv_suffix_alias']
                current = float(mag['setI'])
                coeffs = numpy.append(value['field_integral_coefficients'][:-1],
                                      value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = speed_of_light * int_strength / self.total_energy_gain
                # self.update_widgets_with_values("lattice:" + key + ":k1l", effect / value['magnetic_length'])
                value['k1l'] = effect / value['magnetic_length']
            elif value['type'] == 'solenoid':
                sol_pv_alias = key + ":" + value['pv_suffix_alias']
                current = float(mag['setI'])
                sign = numpy.copysign(1, current)
                coeffs = numpy.append(value['field_integral_coefficients'][-4:-1] * int(sign),
                                      value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = int_strength / value['magnetic_length']
                value['field_amplitude'] = float(effect / value['magnetic_length'])
            magnetdata[mag['name']] = mag
        # print(magnetdata)
        return magnetdata

    def read_values_from_epics(self, dict, time_from=None, time_to=None):
        """Extrtact values from an EPICS PV and update the dictionary."""
        self.total_energy_gain = self.get_energy_gain(time_from, time_to)
        speed_of_light = scipy.constants.speed_of_light / 1e6
        for key, value in dict.items():
            if value['type'] == 'quadrupole':
                quad_pv_alias = key + ":" + value['pv_suffix_alias']
                current = self.read_values_from_archiver(quad_pv_alias, time_from, time_to)
                coeffs = numpy.append(value['field_integral_coefficients'][:-1],
                                      value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = speed_of_light * int_strength / self.total_energy_gain
                value['k1l'] = effect / value['magnetic_length']
            elif value['type'] == 'solenoid':
                sol_pv_alias = key + ":" + value['pv_suffix_alias']
                current = self.read_values_from_archiver(sol_pv_alias, time_from, time_to)
                sign = numpy.copysign(1, current)
                coeffs = numpy.append(value['field_integral_coefficients'][-4:-1] * int(sign),
                                      value['field_integral_coefficients'][-1])
                int_strength = numpy.polyval(coeffs, current)
                effect = int_strength / value['magnetic_length']
                value['field_amplitude'] = float(effect / value['magnetic_length'])
            elif value['type'] == 'generator':
                if key == 'charge':
                    charge_pv_alias = value['pv_root_alias'] + ":" + value['pv_suffix_alias']
                    charge = self.read_values_from_archiver(charge_pv_alias, time_from, time_to)
                    value['value'] = charge * 1e-3

    def get_energy_from_rf(self, klystron_power, phase, pulse_length):
        """Return the estimated energy gain from an RF cavity for the given RF parameters."""
        bestcase = 0.407615 + 1.94185 * (((1 - math.exp((-1.54427 * 10 ** 6 * pulse_length * 10 ** -6))) * (
                    0.0331869 + 6.05422 * 10 ** -7 * klystron_power)) * numpy.cos(phase)) ** 0.5
        worstcase = 0.377 + 1.81689 * (((1 - math.exp((-1.54427 * 10 ** 6 * pulse_length * 10 ** -6))) * (
                    0.0331869 + 6.05422 * 10 ** -7 * klystron_power)) * numpy.cos(phase)) ** 0.5
        return numpy.mean([bestcase, worstcase])
