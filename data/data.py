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

        if initialise:
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

    def get_framework(self):
        """Return the framework object."""
        return self.Framework

    def get_data(self):
        """Initialise element dictionaries and prepare them for the framework values."""
        self.scan_parameter = collections.OrderedDict()
        self.parameterDict.get_data(self.Framework)

    def initialise_data(self):
        """Initialise the element dictionaries and keys with data from the framework."""
        self.parameterDict.initialise_data()
        self.quad_values = self.parameterDict.quad_values
        self.rf_values = self.parameterDict.rf_values
        self.update_mag_field_coefficients()

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

    def update_mag_field_coefficients(self):
        """Update magnet field coefficients in the relevant dictionaries."""
        s02ficq1 = [-2.23133410405682E-10, 4.5196171252132E-08, -3.46208258004659E-06, 1.11195870210961E-04,
                    2.38129337415767E-02, 9.81229429460256E-03]
        s02ficq2 = [-4.69068497199892E-10, 7.81236692669882E-08, -4.99557108021749E-06, 1.39687166906618E-04,
                    2.32819099224878E-02, 9.77695097574923E-03]
        s02ficq3 = [-4.01132756980213E-10, 7.04774652367448E-08, -4.7303680012511E-06, 1.37571730391246E-04,
                    2.33327839789932E-02, 9.49568371388574E-03]
        s02ficq4 = [-3.12868198002574E-10, 5.87771428279647E-08, -4.18748562338666E-06, 1.27524427731924E-04,
                    2.34218216296292E-02, 9.38588316008555E-03]
        c2vficq1 = [-1.30185900474931E-11, 5.70352698264348E-09, -9.08937880373639E-07, 6.03053164909332E-05,
                    0.014739040805921, 1.37593271780352E-02]
        c2vficq2 = [-1.30779403854705E-11, 5.72293796261772E-09, -9.08645007418186E-07, 5.97762384752619E-05,
                    1.47596073775721E-02, 1.58516912403471E-02]
        c2vficq3 = [-1.31651924239548E-11, 5.76805215137824E-09, -9.16843633799561E-07, 6.036266595182E-05,
                    1.47634437187611E-02, 0.013343693771224]
        ebtficq7 = [-1.51802828278694E-05, 0.000208236492203741, 0.102224127676636, 0.00205656183129602]
        ebtficq8 = [-3.06357099595939E-05, 0.000442533546326552, 0.101577009522434, 0.00146589509380893]
        ebtficq9 = [0.111939163037871, -0.00132252769474545]
        ebtficq10 = [0.111966157109812, -0.00170732356716569]
        ebtficq11 = [0.112072763436341, -0.00182025848896622]
        ebtficq15 = [0.111954754, -0.001381788]
        ba1ficq1 = [1.59491, -0.01760]
        ba1ficq2 = [1.59214, -0.01508]
        ba1ficq3 = [1.59020, -0.01823]
        ba1ficq4 = [1.58881, -0.01033]
        ba1ficq5 = [1.59298, -0.02111]
        ba1ficq6 = [1.58624, 0.00451]
        ba1ficq7 = [0.36799, 0.00144]
        lrgbsolfic = [0.000513431, -1.27695e-7, 1.61655e-10, -0.032733798, -4.29885e-06, 2.28967e-08, 0.001833327,
                      -2.5354e-06, -1.04715e-09, -1.61177e-12, -2.94837e-05, 2.13938e-07, -0.003957362, 0.246073139,
                      -4.393602393, 0.0]
        lrgsolfic = [2.17321571, -0.858179277, 0.172127130, -0.0171033399, 6.70371530e-04, -3.53922e-08,
                     1.53138e-05, 0.167819191, 0.0]
        l01sol1fic = [0.911580969, -0.0374385376, 0.00106926073, -1.64644381e-05, 1.01769629e-07, 0, 0, 0.37651102,
                      0.12171419]
        l01sol2fic = [0.847688880, -0.0653499119, 0.00243270133, -4.29020066e-05, 2.87019853e-07, 0, 0, 0.37651102,
                      0.12171419]
        s02mlq1 = 128.68478212775
        s02mlq2 = 126.817287248819
        s02mlq3 = 127.241994829126
        s02mlq4 = 127.421664936758
        c2vmlq1 = 121.567272525393
        c2vmlq2 = 121.511900610076
        c2vmlq3 = 121.550749828396
        ebtmlq7 = 125.299909233924
        ebtmlq8 = 125.27558356645
        ebtmlq9 = 70.4236023746139
        ebtmlq10 = 70.4236023746139
        ebtmlq11 = 70.4236023746139
        ebtmlq15 = 70.4236023746139
        ba1mlq1 = 70.4236023746139
        ba1mlq2 = 70.4236023746139
        ba1mlq3 = 70.4236023746139
        ba1mlq4 = 70.4236023746139
        ba1mlq5 = 70.4236023746139
        ba1mlq6 = 70.4236023746139
        ba1mlq7 = 70.4236023746139
        lrgbsolml = 12.5
        lrgsolml = 139.50
        l01sol1ml = 726.91820512820505
        l01sol2ml = 726.91820512820505
        self.quad_values['CLA-S02-MAG-QUAD-01'].update(
            {'field_integral_coefficients': s02ficq1})
        self.quad_values['CLA-S02-MAG-QUAD-02'].update(
            {'field_integral_coefficients': s02ficq2})
        self.quad_values['CLA-S02-MAG-QUAD-03'].update(
            {'field_integral_coefficients': s02ficq3})
        self.quad_values['CLA-S02-MAG-QUAD-04'].update(
            {'field_integral_coefficients': s02ficq4})
        self.quad_values['CLA-C2V-MAG-QUAD-01'].update(
            {'field_integral_coefficients': c2vficq1})
        self.quad_values['CLA-C2V-MAG-QUAD-02'].update(
            {'field_integral_coefficients': c2vficq2})
        self.quad_values['CLA-C2V-MAG-QUAD-03'].update(
            {'field_integral_coefficients': c2vficq3})
        self.quad_values['EBT-INJ-MAG-QUAD-07'].update(
            {'field_integral_coefficients': ebtficq7})
        self.quad_values['EBT-INJ-MAG-QUAD-08'].update(
            {'field_integral_coefficients': ebtficq8})
        self.quad_values['EBT-INJ-MAG-QUAD-09'].update(
            {'field_integral_coefficients': ebtficq9})
        self.quad_values['EBT-INJ-MAG-QUAD-10'].update(
            {'field_integral_coefficients': ebtficq10})
        self.quad_values['EBT-INJ-MAG-QUAD-11'].update(
            {'field_integral_coefficients': ebtficq11})
        self.quad_values['EBT-INJ-MAG-QUAD-15'].update(
            {'field_integral_coefficients': ebtficq15})
        self.quad_values['EBT-BA1-MAG-QUAD-01'].update(
            {'field_integral_coefficients': ba1ficq1})
        self.quad_values['EBT-BA1-MAG-QUAD-02'].update(
            {'field_integral_coefficients': ba1ficq2})
        self.quad_values['EBT-BA1-MAG-QUAD-03'].update(
            {'field_integral_coefficients': ba1ficq3})
        self.quad_values['EBT-BA1-MAG-QUAD-04'].update(
            {'field_integral_coefficients': ba1ficq4})
        self.quad_values['EBT-BA1-MAG-QUAD-05'].update(
            {'field_integral_coefficients': ba1ficq5})
        self.quad_values['EBT-BA1-MAG-QUAD-06'].update(
            {'field_integral_coefficients': ba1ficq6})
        self.quad_values['EBT-BA1-MAG-QUAD-07'].update(
            {'field_integral_coefficients': ba1ficq7})
        self.rf_values['CLA-LRG1-MAG-SOL-01'].update(
            {'field_integral_coefficients': lrgsolfic})
        self.rf_values['CLA-LRG1-MAG-BSOL-01'].update(
            {'field_integral_coefficients': lrgbsolfic})
        self.rf_values['CLA-L01-MAG-SOL-01'].update(
            {'field_integral_coefficients': l01sol1fic})
        self.rf_values['CLA-L01-MAG-SOL-02'].update(
            {'field_integral_coefficients': l01sol2fic})
        self.quad_values['CLA-S02-MAG-QUAD-01'].update({'magnetic_length': s02mlq1})
        self.quad_values['CLA-S02-MAG-QUAD-02'].update({'magnetic_length': s02mlq2})
        self.quad_values['CLA-S02-MAG-QUAD-03'].update({'magnetic_length': s02mlq3})
        self.quad_values['CLA-S02-MAG-QUAD-04'].update({'magnetic_length': s02mlq4})
        self.quad_values['CLA-C2V-MAG-QUAD-01'].update({'magnetic_length': c2vmlq1})
        self.quad_values['CLA-C2V-MAG-QUAD-02'].update({'magnetic_length': c2vmlq2})
        self.quad_values['CLA-C2V-MAG-QUAD-03'].update({'magnetic_length': c2vmlq3})
        self.quad_values['EBT-INJ-MAG-QUAD-07'].update({'magnetic_length': ebtmlq7})
        self.quad_values['EBT-INJ-MAG-QUAD-08'].update({'magnetic_length': ebtmlq8})
        self.quad_values['EBT-INJ-MAG-QUAD-09'].update({'magnetic_length': ebtmlq9})
        self.quad_values['EBT-INJ-MAG-QUAD-10'].update({'magnetic_length': ebtmlq10})
        self.quad_values['EBT-INJ-MAG-QUAD-11'].update({'magnetic_length': ebtmlq11})
        self.quad_values['EBT-INJ-MAG-QUAD-15'].update({'magnetic_length': ebtmlq15})
        self.quad_values['EBT-BA1-MAG-QUAD-01'].update({'magnetic_length': ba1mlq1})
        self.quad_values['EBT-BA1-MAG-QUAD-02'].update({'magnetic_length': ba1mlq2})
        self.quad_values['EBT-BA1-MAG-QUAD-03'].update({'magnetic_length': ba1mlq3})
        self.quad_values['EBT-BA1-MAG-QUAD-04'].update({'magnetic_length': ba1mlq4})
        self.quad_values['EBT-BA1-MAG-QUAD-05'].update({'magnetic_length': ba1mlq5})
        self.quad_values['EBT-BA1-MAG-QUAD-06'].update({'magnetic_length': ba1mlq6})
        self.quad_values['EBT-BA1-MAG-QUAD-07'].update({'magnetic_length': ba1mlq7})
        self.rf_values['CLA-LRG1-MAG-SOL-01'].update({'magnetic_length': lrgsolml})
        self.rf_values['CLA-LRG1-MAG-BSOL-01'].update({'magnetic_length': lrgbsolml})
        self.rf_values['CLA-L01-MAG-SOL-01'].update({'magnetic_length': l01sol1ml})
        self.rf_values['CLA-L01-MAG-SOL-02'].update({'magnetic_length': l01sol2ml})
